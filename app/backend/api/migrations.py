"""Forward-only migrations applied after the legacy bootstrap schema.

Migrations 001--007 predate the ledger and are represented as a verified
baseline because `init_db` already provides their final compatible schema.
New migrations are applied once, with a checksum, inside the caller's
transaction. A checksum mismatch is a deployment stop: edited history is not
safe to replay.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
BASELINE_MIGRATIONS = {
    "001_indexes.sql",
    "002_user_id.sql",
    "003_attempts_extra.sql",
    "004_fsrs.sql",
    "004_fts5.sql",
    "005_performance_observability.sql",
    "007_institution_index.sql",
}
MIGRATION_NAME = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _statements(path: Path) -> list[str]:
    """Split the deliberately simple, repository-owned SQLite migrations."""
    sql = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def apply_pending_migrations(db) -> list[str]:
    db.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)
    known = {
        row["migration_id"]: row["checksum"]
        for row in db.execute("SELECT migration_id, checksum FROM schema_migrations").fetchall()
    }
    now = datetime.now(timezone.utc).isoformat()
    applied: list[str] = []

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if not MIGRATION_NAME.fullmatch(path.name):
            continue
        checksum = _checksum(path)
        existing = known.get(path.name)
        if existing and existing != checksum:
            raise RuntimeError(f"Migration checksum changed after application: {path.name}")
        if existing:
            continue
        if path.name in BASELINE_MIGRATIONS:
            db.execute(
                "INSERT INTO schema_migrations (migration_id, checksum, applied_at, source) VALUES (?, ?, ?, ?)",
                (path.name, checksum, now, "legacy-bootstrap-baseline"),
            )
            continue
        for statement in _statements(path):
            db.execute(statement)
        db.execute(
            "INSERT INTO schema_migrations (migration_id, checksum, applied_at, source) VALUES (?, ?, ?, ?)",
            (path.name, checksum, now, "forward-migration"),
        )
        applied.append(path.name)
    return applied
