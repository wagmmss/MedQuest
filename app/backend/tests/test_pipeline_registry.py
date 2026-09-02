from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from scripts.pipeline import inventory, load_manifest


def test_manifest_classifies_unlisted_scripts_as_legacy() -> None:
    report = inventory(load_manifest())
    assert report["total_python_scripts"] >= 300
    assert report["critical"] == 2
    assert report["important"] == 1
    assert report["legacy"] > 0
    assert report["unclassified"] == []


def test_runner_rejects_unknown_pipeline() -> None:
    script = Path(__file__).parents[1] / "scripts" / "pipeline.py"
    result = subprocess.run([sys.executable, str(script), "run", "sync-to-production"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Unknown or legacy pipeline" in result.stderr


def test_runner_records_readonly_run(tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.db"
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE job_runs (
            id TEXT PRIMARY KEY, pipeline_id TEXT, pipeline_version TEXT, status TEXT,
            input_hash TEXT, output_hash TEXT, started_at TEXT, finished_at TEXT,
            duration_ms INTEGER, actor TEXT, summary_json TEXT, error_class TEXT
        );
    """)
    db.close()
    script = Path(__file__).parents[1] / "scripts" / "pipeline.py"
    result = subprocess.run(
        [sys.executable, str(script), "run", "taxonomy-sync", "--db", str(db_path)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
    )
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(db_path) as checked:
        row = checked.execute("SELECT pipeline_id, status, summary_json FROM job_runs").fetchone()
    assert row[0:2] == ("taxonomy-sync", "dry_run")
    assert json.loads(row[2])["returncode"] == 0
