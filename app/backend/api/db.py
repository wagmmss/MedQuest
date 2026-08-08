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
        
    def execute(self, sql, parameters=()):
        # Replace ? with ? in SQL? libsql_client supports ? syntax but prefers list of args
        # Ensure parameters is a list/tuple
        args = list(parameters)
        clean_args = [x if not isinstance(x, bytes) else x.decode('utf-8', 'ignore') for x in args]
        try:
            result = self.client.execute(sql, clean_args)
            return TursoCursor(result)
        except Exception as e:
            logger.error(f"Turso Error on query: {sql} with args {clean_args}. Error: {e}")
            raise
            
    def commit(self):
        # HTTP client is auto-commit or we can ignore
        pass
        
    def close(self):
        self.client.close()

def get_db():
    if "db" not in g:
        if TURSO_URL and TURSO_TOKEN:
            import libsql_client
            # Se for ws:// muda pra https:// pro client sync HTTP
            url = TURSO_URL.replace("libsql://", "https://")
            client = libsql_client.create_client_sync(url=url, auth_token=TURSO_TOKEN)
            g.db = TursoConnection(client)
        else:
            g.db = sqlite3.connect(DB_PATH, timeout=10)
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
        db.execute("CREATE TABLE IF NOT EXISTS favorites (question_id INTEGER PRIMARY KEY, user_id TEXT DEFAULT '1')")
        db.execute("""CREATE TABLE IF NOT EXISTS spaced_repetition (
            question_id INTEGER PRIMARY KEY, efactor REAL, interval INTEGER,
            next_review_date TEXT, user_id TEXT DEFAULT '1', fsrs_card TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS planner_progress (
            week INTEGER PRIMARY KEY, studied INTEGER DEFAULT 0, studied_at TEXT,
            rev24h INTEGER DEFAULT 0, rev7d INTEGER DEFAULT 0, rev30d INTEGER DEFAULT 0,
            user_id TEXT DEFAULT '1')""")
        db.execute("""CREATE TABLE IF NOT EXISTS planner_config (
            id INTEGER PRIMARY KEY CHECK (id = 1), exam_date TEXT, start_date TEXT,
            days_per_week INTEGER DEFAULT 6, questions_per_day INTEGER DEFAULT 30,
            updated_at TEXT, user_id TEXT DEFAULT '1')""")
        db.execute("""CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            front TEXT NOT NULL,
            back TEXT,
            created_at TEXT NOT NULL,
            next_review_date TEXT,
            fsrs_card TEXT,
            user_id TEXT DEFAULT '1')""")

        try:
            if isinstance(db, TursoConnection):
                tables = [r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            else:
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                
            if "attempts" in tables:
                ac = _table_cols(db, "attempts")
                for col, ddl in [("user_id", "TEXT DEFAULT '1'"), ("time_spent_ms", "INTEGER"), ("confidence", "TEXT")]:
                    if col not in ac:
                        try:
                            db.execute(f"ALTER TABLE attempts ADD COLUMN {col} {ddl}")
                        except Exception:
                            pass
            if "fsrs_card" not in _table_cols(db, "spaced_repetition"):
                try:
                    db.execute("ALTER TABLE spaced_repetition ADD COLUMN fsrs_card TEXT")
                except Exception:
                    pass
            db.commit()
        except Exception as e:
            logger.error(f"Error during init_db: {e}")
