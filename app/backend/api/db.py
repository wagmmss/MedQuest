"""Acesso ao banco (SQLite) e criação/evolução de tabelas."""
import os
import sqlite3

from flask import g

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(BACKEND_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
# MEDQUEST_DB permite apontar para um banco de teste.
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))


def get_db():
    if "db" not in g:
        path = os.environ.get("MEDQUEST_DB", DB_PATH)
        g.db = sqlite3.connect(path, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")  # espera locks em vez de falhar
        try:
            g.db.execute("PRAGMA journal_mode = WAL")  # leitura/escrita concorrentes
        except sqlite3.OperationalError:
            pass
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _table_cols(db, table):
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]


def init_db(app):
    """Cria tabelas de usuário se não existirem e garante colunas novas (idempotente)."""
    with app.app_context():
        db = get_db()
        db.execute("CREATE TABLE IF NOT EXISTS favorites (question_id INTEGER PRIMARY KEY, user_id INTEGER DEFAULT 1)")
        db.execute("""CREATE TABLE IF NOT EXISTS spaced_repetition (
            question_id INTEGER PRIMARY KEY, efactor REAL, interval INTEGER,
            next_review_date TEXT, user_id INTEGER DEFAULT 1, fsrs_card TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS planner_progress (
            week INTEGER PRIMARY KEY, studied INTEGER DEFAULT 0, studied_at TEXT,
            rev24h INTEGER DEFAULT 0, rev7d INTEGER DEFAULT 0, rev30d INTEGER DEFAULT 0,
            user_id INTEGER DEFAULT 1)""")
        db.execute("""CREATE TABLE IF NOT EXISTS planner_config (
            id INTEGER PRIMARY KEY CHECK (id = 1), exam_date TEXT, start_date TEXT,
            days_per_week INTEGER DEFAULT 6, questions_per_day INTEGER DEFAULT 30,
            updated_at TEXT, user_id INTEGER DEFAULT 1)""")

        # Colunas novas em bancos já existentes
        if "attempts" in [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
            ac = _table_cols(db, "attempts")
            for col, ddl in [("user_id", "INTEGER DEFAULT 1"), ("time_spent_ms", "INTEGER"), ("confidence", "TEXT")]:
                if col not in ac:
                    db.execute(f"ALTER TABLE attempts ADD COLUMN {col} {ddl}")
        if "fsrs_card" not in _table_cols(db, "spaced_repetition"):
            db.execute("ALTER TABLE spaced_repetition ADD COLUMN fsrs_card TEXT")
        db.commit()
