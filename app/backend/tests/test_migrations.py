from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from api.migrations import apply_pending_migrations


def test_migrations_create_ledger_and_job_runs_after_bootstrap(app) -> None:
    with app.app_context():
        from api.db import get_db

        db = get_db()
        rows = db.execute("SELECT migration_id, checksum FROM schema_migrations ORDER BY migration_id").fetchall()
        assert {row["migration_id"] for row in rows} >= {
            "006_classification_review.sql",
            "008_job_runs.sql",
            "009_flashcards_allow_unlinked.sql",
        }
        assert all(len(row["checksum"]) == 64 for row in rows)
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_runs'").fetchone()


def test_flashcard_migration_allows_unlinked_anki_cards(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_flashcards.db"
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE questions (id INTEGER PRIMARY KEY)")
    db.execute("""
        CREATE TABLE flashcards (
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
            report_status TEXT,
            deck_name TEXT DEFAULT 'Geral',
            tags TEXT,
            source_type TEXT DEFAULT 'medquest',
            anki_nid INTEGER
        )
    """)
    db.execute("""
        INSERT INTO flashcards (question_id, front, created_at, user_id)
        VALUES (1, 'cartão existente', '2026-01-01T00:00:00+00:00', 'user-1')
    """)

    apply_pending_migrations(db)

    columns = {row["name"]: row for row in db.execute("PRAGMA table_info(flashcards)").fetchall()}
    assert columns["question_id"]["notnull"] == 0
    db.execute("""
        INSERT INTO flashcards (question_id, front, created_at, user_id, source_type)
        VALUES (NULL, 'cartão do Anki', '2026-01-01T00:00:00+00:00', 'user-1', 'anki_connect')
    """)
    assert db.execute("SELECT COUNT(*) AS count FROM flashcards").fetchone()["count"] == 2
    db.close()


def test_applied_migration_checksum_cannot_change(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.db"
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE questions (id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE alternatives (id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE explanations (question_id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE question_images (id INTEGER PRIMARY KEY, question_id INTEGER)")
    db.execute("CREATE TABLE attempts (id INTEGER PRIMARY KEY, user_id TEXT, question_id INTEGER, answered_at TEXT)")
    db.execute("CREATE TABLE spaced_repetition (question_id INTEGER, user_id TEXT, next_review_date TEXT)")
    db.execute("CREATE TABLE favorites (question_id INTEGER, user_id TEXT)")
    db.execute("CREATE TABLE planner_progress (week INTEGER, user_id TEXT)")
    db.execute("""
        CREATE TABLE flashcards (
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
            report_status TEXT,
            deck_name TEXT DEFAULT 'Geral',
            tags TEXT,
            source_type TEXT DEFAULT 'medquest',
            anki_nid INTEGER
        )
    """)
    apply_pending_migrations(db)
    db.execute("UPDATE schema_migrations SET checksum='changed' WHERE migration_id='008_job_runs.sql'")
    db.commit()
    with pytest.raises(RuntimeError, match="checksum changed"):
        apply_pending_migrations(db)
    db.close()
