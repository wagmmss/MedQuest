"""Acesso ao banco (SQLite / Turso) e criação/evolução de tabelas."""
import logging
import os
import sqlite3
from contextlib import contextmanager
from threading import local

from dotenv import load_dotenv
from flask import g

from .migrations import apply_pending_migrations

load_dotenv()

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

# The native libSQL client owns a Rust runtime and must not be shared across
# request threads. Keep one persistent connection per worker thread instead of
# constructing/closing a runtime for every Flask request.
_turso_clients = local()


def _connect_turso(turso_url, turso_token):
    import libsql

    client = getattr(_turso_clients, "client", None)
    if client is None:
        # A direct remote connection avoids the full embedded-replica sync at
        # cold start. Its lifetime is the worker thread, not a request.
        client = libsql.connect(turso_url, auth_token=turso_token)
        _turso_clients.client = client
        logger.info("Connected to remote Turso database directly for worker thread")
    return client


def _is_stale_turso_stream(error):
    """Whether Turso rejected a request before it could run on an expired stream."""
    return "stream not found" in str(error).lower()


def _reconnect_turso(turso_url, turso_token, failed_client):
    """Discard only the current worker's invalid client and open a fresh stream."""
    if getattr(_turso_clients, "client", None) is failed_client:
        delattr(_turso_clients, "client")
    try:
        failed_client.close()
    except Exception:
        # The stream is already invalid; closing it is best-effort cleanup.
        pass
    return _connect_turso(turso_url, turso_token)

class TursoCursor:
    """Expose DB-API cursor rows as mappings, matching sqlite3.Row usage."""

    def __init__(self, cursor):
        self.cursor = cursor
        self.columns = [column[0] for column in (cursor.description or [])]
        self._closed = False
        
    def __del__(self):
        self.close()
        
    def fetchone(self):
        row = self.cursor.fetchone()
        self.close()
        if row is None:
            return None
        return dict(zip(self.columns, row))
        
    def fetchall(self):
        rows = self.cursor.fetchall()
        self.close()
        return [dict(zip(self.columns, row)) for row in rows]

    def close(self):
        if getattr(self, '_closed', True):
            return
        close_method = getattr(self.cursor, "close", None)
        if callable(close_method):
            close_method()
        self._closed = True
        
    @property
    def lastrowid(self):
        return getattr(self.cursor, "lastrowid", None)

    @property
    def rowcount(self):
        return getattr(self.cursor, "rowcount", 0)

class TursoConnection:
    def __init__(self, client, persistent=False, reconnect=None):
        self.client = client
        self.tx = False
        self.persistent = persistent
        self._reconnect = reconnect

    def _execute_with_reconnect(self, sql, args, retry_stale_stream):
        try:
            return self.client.execute(sql, args)
        except Exception as error:
            # A 404 "stream not found" is produced by Turso before the SQL is
            # evaluated. It is therefore safe to recreate the client and replay
            # a single statement, but never while a transaction is in progress:
            # replaying part of a transaction could duplicate a mutation.
            if not (retry_stale_stream and self.persistent and self._reconnect and _is_stale_turso_stream(error)):
                raise
            logger.warning("Turso stream expired; reconnecting and retrying one statement")
            self.client = self._reconnect(self.client)
            return self.client.execute(sql, args)
        
    def begin(self, immediate=False):
        if self.tx:
            raise RuntimeError("A Turso transaction is already active")
        self._execute_with_reconnect("BEGIN IMMEDIATE" if immediate else "BEGIN", (), retry_stale_stream=True)
        self.tx = True

    def execute(self, sql, parameters=()):
        args = list(parameters)
        clean_args = [x if not isinstance(x, bytes) else x.decode('utf-8', 'ignore') for x in args]
        try:
            cursor = self._execute_with_reconnect(sql, clean_args, retry_stale_stream=not self.tx)
            return TursoCursor(cursor)
        except Exception as e:
            logger.error("Turso query failed: %s", e)
            raise

    def batch(self, queries):
        res = []
        for sql, parameters in queries:
            res.append(self.execute(sql, parameters))
        return res
            
    def commit(self):
        try:
            self.client.commit()
        finally:
            self.tx = False
                
    def rollback(self):
        try:
            self.client.rollback()
        except Exception:
            pass
        finally:
            self.tx = False
        
    def close(self):
        if self.tx:
            self.rollback()
        if not self.persistent:
            self.client.close()

@contextmanager
def db_transaction(db, immediate=False):
    """Context manager para gerenciar transações e garantir rollback explícito."""
    try:
        if isinstance(db, TursoConnection):
            db.begin(immediate=immediate)
        else:
            db.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

def get_db():
    from flask import current_app
    if "db" not in g:
        is_testing = current_app.config.get("TESTING", False)
        turso_url = os.environ.get("TURSO_DATABASE_URL")
        turso_token = os.environ.get("TURSO_AUTH_TOKEN")
        
        if not is_testing and bool(turso_url) != bool(turso_token):
            raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be configured together")

        if turso_url and turso_token and not is_testing:
            if not turso_url.lower().startswith(("libsql://", "wss://")):
                raise ValueError("TURSO_DATABASE_URL must use libsql:// or wss:// for transaction support")
            client = _connect_turso(turso_url, turso_token)
            g.db = TursoConnection(
                client,
                persistent=True,
                reconnect=lambda failed_client: _reconnect_turso(turso_url, turso_token, failed_client),
            )
        else:
            db_path = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
            g.db = sqlite3.connect(db_path, timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.execute("PRAGMA busy_timeout = 10000")
            try:
                g.db.execute("PRAGMA journal_mode = WAL")
                g.db.execute("PRAGMA synchronous = NORMAL")
                g.db.execute("PRAGMA cache_size = -64000")
                g.db.execute("PRAGMA mmap_size = 268435456")
                g.db.execute("PRAGMA temp_store = MEMORY")
            except sqlite3.OperationalError as e:
                logger.warning(f"Failed to set SQLite performance pragmas: {e}")
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        if exception:
            if hasattr(db, "rollback"):
                db.rollback()
            else:
                db.execute("ROLLBACK") if hasattr(db, "in_transaction") and getattr(db, "in_transaction", False) else None
        db.close()

def _table_cols(db, table):
    if isinstance(db, TursoConnection):
        res = db.execute(f"PRAGMA table_info({table})").fetchall()
        return [r["name"] for r in res]
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]

def init_db(app):
    """Cria tabelas de usuário se não existirem e garante colunas novas."""
    with app.app_context():
        db = get_db()
        with db_transaction(db, immediate=True):
            db.execute("""CREATE TABLE IF NOT EXISTS questions(
                id INTEGER PRIMARY KEY, source_file TEXT, source_number INTEGER, year INTEGER,
                institution_code TEXT, institution_label TEXT, topic TEXT, stem TEXT,
                correct_letter TEXT, missing_alts INTEGER DEFAULT 0, area TEXT, subtema TEXT,
                subtema_id TEXT, subtema_orig TEXT, editorial_status TEXT, status TEXT DEFAULT 'active')""")
            db.execute("""CREATE TABLE IF NOT EXISTS alternatives(
                id INTEGER PRIMARY KEY, question_id INTEGER, letter TEXT,
                text TEXT, is_correct INTEGER)""")
            db.execute("""CREATE TABLE IF NOT EXISTS explanations(
                question_id INTEGER PRIMARY KEY, explanation_text TEXT, generated_at TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS question_images(
                id INTEGER PRIMARY KEY, question_id INTEGER, file_path TEXT, order_index INTEGER)""")
            db.execute("""CREATE TABLE IF NOT EXISTS attempts(
                id INTEGER PRIMARY KEY, question_id INTEGER, selected_letter TEXT,
                is_correct INTEGER, answered_at TEXT, confidence TEXT, user_id TEXT DEFAULT '1', time_spent_ms INTEGER)""")

            db.execute("CREATE TABLE IF NOT EXISTS favorites (question_id INTEGER, user_id TEXT DEFAULT '1', PRIMARY KEY (question_id, user_id))")
            db.execute("""CREATE TABLE IF NOT EXISTS spaced_repetition (
                question_id INTEGER, efactor REAL, interval INTEGER,
                next_review_date TEXT, user_id TEXT DEFAULT '1', fsrs_card TEXT,
                PRIMARY KEY (question_id, user_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS planner_progress (
                week INTEGER, studied INTEGER DEFAULT 0, studied_at TEXT,
                rev24h INTEGER DEFAULT 0, rev7d INTEGER DEFAULT 0, rev30d INTEGER DEFAULT 0,
                 user_id TEXT DEFAULT '1', PRIMARY KEY (week, user_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS planner_topic_progress (
                week INTEGER NOT NULL, subtema TEXT NOT NULL, completed INTEGER DEFAULT 0,
                completed_at TEXT, user_id TEXT DEFAULT '1',
                PRIMARY KEY (week, subtema, user_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS planner_config (
                user_id TEXT PRIMARY KEY, exam_date TEXT, start_date TEXT,
                days_per_week INTEGER DEFAULT 6, questions_per_day INTEGER DEFAULT 30, hours_per_day INTEGER DEFAULT 4, target_score REAL,
                target_institution TEXT, target_specialty TEXT,
                updated_at TEXT)""")
            existing_pc_cols = _table_cols(db, "planner_config")
            if "target_score" not in existing_pc_cols:
                db.execute("ALTER TABLE planner_config ADD COLUMN target_score REAL")
            if "target_institution" not in existing_pc_cols:
                db.execute("ALTER TABLE planner_config ADD COLUMN target_institution TEXT")
            if "target_specialty" not in existing_pc_cols:
                db.execute("ALTER TABLE planner_config ADD COLUMN target_specialty TEXT")
            if "hours_per_day" not in existing_pc_cols:
                db.execute("ALTER TABLE planner_config ADD COLUMN hours_per_day INTEGER DEFAULT 4")

            db.execute("""CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT,
                created_at TEXT NOT NULL,
                next_review_date TEXT,
                fsrs_card TEXT,
                user_id TEXT DEFAULT '1',
                source_context TEXT,
                is_ai_generated INTEGER DEFAULT 0,
                report_status TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS simulado_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, client_session_id TEXT NOT NULL,
                planned_duration_seconds INTEGER NOT NULL, elapsed_seconds INTEGER NOT NULL,
                total_questions INTEGER NOT NULL, answered_count INTEGER NOT NULL, correct_count INTEGER NOT NULL,
                filters_json TEXT NOT NULL, area_results_json TEXT NOT NULL, completed_at TEXT NOT NULL,
                user_id TEXT DEFAULT '1', UNIQUE(user_id, client_session_id))""")
            existing_fc_cols = _table_cols(db, "flashcards")
            if "source_context" not in existing_fc_cols:
                db.execute("ALTER TABLE flashcards ADD COLUMN source_context TEXT")
            if "is_ai_generated" not in existing_fc_cols:
                db.execute("ALTER TABLE flashcards ADD COLUMN is_ai_generated INTEGER DEFAULT 0")
            if "report_status" not in existing_fc_cols:
                db.execute("ALTER TABLE flashcards ADD COLUMN report_status TEXT")
            
            db.execute("""CREATE TABLE IF NOT EXISTS clinical_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stem TEXT NOT NULL,
                images TEXT,
                medical_references TEXT)""")
            
            db.execute("""CREATE TABLE IF NOT EXISTS learning_sessions (
                user_id TEXT NOT NULL,
                session_type TEXT NOT NULL,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, session_type))""")

            db.execute("""CREATE TABLE IF NOT EXISTS idempotency_keys (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                status_code INTEGER,
                response_body TEXT,
                lease_expires_at REAL DEFAULT 0,
                lease_owner_token TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, key))""")
            existing_cols = _table_cols(db, "idempotency_keys")
            if "status" not in existing_cols:
                db.execute("ALTER TABLE idempotency_keys ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
            if "lease_expires_at" not in existing_cols:
                db.execute("ALTER TABLE idempotency_keys ADD COLUMN lease_expires_at REAL DEFAULT 0")
            if "lease_owner_token" not in existing_cols:
                db.execute("ALTER TABLE idempotency_keys ADD COLUMN lease_owner_token TEXT")

            db.execute("""CREATE TABLE IF NOT EXISTS telemetry_daily_aggregates (
                date TEXT NOT NULL,
                route TEXT NOT NULL,
                method TEXT NOT NULL,
                p50_ms REAL NOT NULL,
                p95_ms REAL NOT NULL,
                p99_ms REAL NOT NULL,
                request_count INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (date, route, method))""")

            db.execute("""CREATE TABLE IF NOT EXISTS notification_configs (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                preferred_hour INTEGER DEFAULT 8,
                days_of_week TEXT DEFAULT '[0,1,2,3,4,5,6]',
                max_daily_reminders INTEGER DEFAULT 1,
                updated_at TEXT)""")

            db.execute("""CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, endpoint))""")

            db.execute("""CREATE TABLE IF NOT EXISTS notification_dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                dispatch_date TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, dispatch_date))""")

            # Indexes that reference migrated columns must be created only
            # after every supported legacy schema has those columns.
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_lease ON idempotency_keys(user_id, lease_expires_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_notification_dispatches_user_date ON notification_dispatches(user_id, dispatch_date)")

            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_question ON attempts (user_id, question_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_question_latest ON attempts (user_id, question_id, id DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_correct ON attempts (user_id, is_correct)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area_subtema ON questions (area, subtema)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_missing_alts ON questions (missing_alts)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_spaced_repetition_review ON spaced_repetition (user_id, next_review_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_flashcards_user_review ON flashcards (user_id, next_review_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_simulado_sessions_user_completed ON simulado_sessions (user_id, completed_at DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area ON questions (area)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_institution ON questions (institution_code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_inst_code_label ON questions (institution_code, institution_label)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_year ON questions (year)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_source ON questions (source_file)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_answered_at ON attempts (answered_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_answered_at ON attempts (user_id, answered_at)")
            apply_pending_migrations(db)

        # FTS is an optional capability and must not invalidate the required schema.
        try:
            with db_transaction(db, immediate=True):
                db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                    stem,
                    explanation
                )""")
        except Exception as e:
            logger.warning("FTS table creation is unavailable: %s", e)
