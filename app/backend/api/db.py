"""Acesso ao banco (SQLite / Turso) e criação/evolução de tabelas."""
import logging
import os
import sqlite3
from contextlib import contextmanager
from threading import local

from dotenv import load_dotenv
from flask import g

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
    def __init__(self, client, persistent=False):
        self.client = client
        self.tx = False
        self.persistent = persistent
        
    def begin(self, immediate=False):
        if self.tx:
            raise RuntimeError("A Turso transaction is already active")
        self.client.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        self.tx = True

    def execute(self, sql, parameters=()):
        args = list(parameters)
        clean_args = [x if not isinstance(x, bytes) else x.decode('utf-8', 'ignore') for x in args]
        try:
            cursor = self.client.execute(sql, clean_args)
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
            g.db = TursoConnection(client, persistent=True)
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
            db.execute("CREATE TABLE IF NOT EXISTS favorites (question_id INTEGER, user_id TEXT DEFAULT '1', PRIMARY KEY (question_id, user_id))")
            db.execute("""CREATE TABLE IF NOT EXISTS spaced_repetition (
                question_id INTEGER, efactor REAL, interval INTEGER,
                next_review_date TEXT, user_id TEXT DEFAULT '1', fsrs_card TEXT,
                PRIMARY KEY (question_id, user_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS planner_progress (
                week INTEGER, studied INTEGER DEFAULT 0, studied_at TEXT,
                rev24h INTEGER DEFAULT 0, rev7d INTEGER DEFAULT 0, rev30d INTEGER DEFAULT 0,
                user_id TEXT DEFAULT '1', PRIMARY KEY (week, user_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS planner_config (
                user_id TEXT PRIMARY KEY, exam_date TEXT, start_date TEXT,
                days_per_week INTEGER DEFAULT 6, questions_per_day INTEGER DEFAULT 30, target_score REAL,
                updated_at TEXT)""")
            existing_pc_cols = _table_cols(db, "planner_config")
            if "target_score" not in existing_pc_cols:
                db.execute("ALTER TABLE planner_config ADD COLUMN target_score REAL")

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

            # Indexes that reference migrated columns must be created only
            # after every supported legacy schema has those columns.
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_lease ON idempotency_keys(user_id, lease_expires_at)")

            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_question ON attempts (user_id, question_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_question_latest ON attempts (user_id, question_id, id DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_correct ON attempts (user_id, is_correct)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area_subtema ON questions (area, subtema)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_missing_alts ON questions (missing_alts)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_spaced_repetition_review ON spaced_repetition (user_id, next_review_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_flashcards_user_review ON flashcards (user_id, next_review_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area ON questions (area)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_institution ON questions (institution_code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_year ON questions (year)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_source ON questions (source_file)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_answered_at ON attempts (answered_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_answered_at ON attempts (user_id, answered_at)")

        # FTS is an optional capability and must not invalidate the required schema.
        try:
            with db_transaction(db, immediate=True):
                db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                    stem,
                    explanation
                )""")
        except Exception as e:
            logger.warning("FTS table creation is unavailable: %s", e)
