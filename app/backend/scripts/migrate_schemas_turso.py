import os

import libsql_client
from dotenv import load_dotenv

load_dotenv()

c = libsql_client.create_client_sync(url=os.environ['TURSO_DATABASE_URL'].replace('libsql://', 'https://'), auth_token=os.environ['TURSO_AUTH_TOKEN'])

tables_to_drop = ['favorites', 'spaced_repetition', 'planner_progress', 'planner_config', 'flashcards']

for table in tables_to_drop:
    print(f"Dropping {table}...")
    try:
        c.execute(f"DROP TABLE IF EXISTS {table}")
    except Exception as e:
        print(f"Error dropping {table}:", e)

print("Creating tables with correct multi-tenant schemas...")

c.execute("CREATE TABLE favorites (question_id INTEGER, user_id TEXT, PRIMARY KEY (question_id, user_id))")
c.execute("""CREATE TABLE spaced_repetition (
    question_id INTEGER, efactor REAL, interval INTEGER,
    next_review_date TEXT, user_id TEXT, fsrs_card TEXT,
    PRIMARY KEY (question_id, user_id))""")
c.execute("""CREATE TABLE planner_progress (
    week INTEGER, studied INTEGER DEFAULT 0, studied_at TEXT,
    rev24h INTEGER DEFAULT 0, rev7d INTEGER DEFAULT 0, rev30d INTEGER DEFAULT 0,
    user_id TEXT, PRIMARY KEY (week, user_id))""")
c.execute("""CREATE TABLE planner_config (
    user_id TEXT PRIMARY KEY, exam_date TEXT, start_date TEXT,
    days_per_week INTEGER DEFAULT 6, questions_per_day INTEGER DEFAULT 30, target_score REAL,
    updated_at TEXT)""")
c.execute("""CREATE TABLE flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    front TEXT NOT NULL,
    back TEXT,
    created_at TEXT NOT NULL,
    next_review_date TEXT,
    fsrs_card TEXT,
    user_id TEXT)""")

print("Migration completed successfully!")
