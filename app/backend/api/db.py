"""Acesso ao banco (SQLite / Turso) e criação/evolução de tabelas."""
import os
import sqlite3
from flask import g
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

class TursoCursor:
    def __init__(self, result):
        self.result = result
        
    def fetchone(self):
        if not self.result.rows:
            return None
        return dict(zip(self.result.columns, self.result.rows[0]))
        
    def fetchall(self):
        if not self.result.rows:
            return []
        return [dict(zip(self.result.columns, r)) for r in self.result.rows]
        
    @property
    def lastrowid(self):
        return getattr(self.result, "last_insert_rowid", None)

class TursoConnection:
    def __init__(self, client):
        self.client = client
        self.tx = None
        
    def _get_tx(self):
        if self.tx is None:
            self.tx = self.client.transaction()
        return self.tx

    def execute(self, sql, parameters=()):
        args = list(parameters)
        clean_args = [x if not isinstance(x, bytes) else x.decode('utf-8', 'ignore') for x in args]
        try:
            tx = self._get_tx()
            result = tx.execute(sql, clean_args)
            return TursoCursor(result)
        except Exception as e:
            logger.error(f"Turso Error on query: {sql} with args {clean_args}. Error: {e}")
            self.rollback()
            raise

    def batch(self, queries):
        res = []
        for sql, parameters in queries:
            res.append(self.execute(sql, parameters))
        return res
            
    def commit(self):
        if self.tx is not None:
            try:
                self.tx.commit()
            finally:
                self.tx = None
                
    def rollback(self):
        if self.tx is not None:
            try:
                self.tx.rollback()
            except Exception:
                pass
            finally:
                self.tx = None
        
    def close(self):
        self.rollback()
        self.client.close()

def get_db():
    from flask import current_app
    if "db" not in g:
        is_testing = current_app.config.get("TESTING", False)
        turso_url = os.environ.get("TURSO_DATABASE_URL")
        turso_token = os.environ.get("TURSO_AUTH_TOKEN")
        
        if turso_url and turso_token and not is_testing:
            import libsql_client
            url = turso_url.replace("libsql://", "https://")
            client = libsql_client.create_client_sync(url=url, auth_token=turso_token)
            g.db = TursoConnection(client)
        else:
            db_path = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
            g.db = sqlite3.connect(db_path, timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.execute("PRAGMA busy_timeout = 10000")
            try:
                g.db.execute("PRAGMA journal_mode = WAL")
            except sqlite3.OperationalError as e:
                logger.warning(f"Failed to set WAL mode: {e}")
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
        try:
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
            db.execute("""CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT,
                created_at TEXT NOT NULL,
                next_review_date TEXT,
                fsrs_card TEXT,
                user_id TEXT DEFAULT '1')""")
            
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
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, key))""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_lease ON idempotency_keys(user_id, lease_expires_at)")

            existing_cols = _table_cols(db, "idempotency_keys")
            if "status" not in existing_cols:
                db.execute("ALTER TABLE idempotency_keys ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
            if "lease_expires_at" not in existing_cols:
                db.execute("ALTER TABLE idempotency_keys ADD COLUMN lease_expires_at REAL DEFAULT 0")

            # FTS5 table
            try:
                db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                    stem,
                    explanation
                )""")
            except Exception as e:
                logger.warning(f"FTS table creation might not be fully supported or already exists: {e}")

            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_question ON attempts (user_id, question_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_correct ON attempts (user_id, is_correct)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area_subtema ON questions (area, subtema)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_spaced_repetition_review ON spaced_repetition (user_id, next_review_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_area ON questions (area)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_institution ON questions (institution_code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_year ON questions (year)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_questions_source ON questions (source_file)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_answered_at ON attempts (answered_at)")
            
            db.commit()
        except Exception as e:
            logger.error(f"Error executing DDL during init_db: {e}")
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error during init_db: {e}")
