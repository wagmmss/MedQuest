from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from scripts.content_repair import apply_repair_plan, build_repair_plan
from scripts.taxonomy_sync import (
    SUBTEMA_MAP_PATH,
    build_subtema_map,
    compile_artifacts,
    render_planner_ts,
)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_content_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY, stem TEXT, correct_letter TEXT,
            missing_alts INTEGER, area TEXT, subtema TEXT,
            institution_code TEXT, year INTEGER, source_file TEXT,
            source_number TEXT, subtema_id TEXT, editorial_status TEXT,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE alternatives (
            id INTEGER PRIMARY KEY, question_id INTEGER, letter TEXT,
            text TEXT, is_correct INTEGER
        );
        CREATE TABLE explanations (
            question_id INTEGER PRIMARY KEY, explanation_text TEXT
        );
        CREATE TABLE question_images (id INTEGER PRIMARY KEY, question_id INTEGER);
        INSERT INTO questions VALUES
            (1,'Valid stem','A',0,'Cirurgia','Trauma Torácico','USP',2024,'a.pdf','1',NULL,NULL,'active'),
            (2,'','A',0,'Cirurgia','Trauma Torácico','USP',2024,'a.pdf','2',NULL,NULL,'active');
        INSERT INTO alternatives(question_id,letter,text,is_correct) VALUES
            (1,'A','alpha',0),(1,'B','beta',1),(1,'C','gamma',0),(1,'D','delta',0),
            (2,'A','alpha',1),(2,'B','beta',0);
        INSERT INTO explanations VALUES (1,'Curta'), (2,'Explicação da alternativa A.');
    """)
    db.commit()
    db.close()


def test_taxonomy_compiler_preserves_existing_ids_and_adds_unique_ids() -> None:
    catalog = [
        {"area": "Cirurgia", "macroThemes": [{"dbSubtemas": ["Existing", "New"]}]},
        {"area": "Cirurgia Geral", "macroThemes": [{"dbSubtemas": ["New"]}]},
    ]
    result = build_subtema_map(catalog, {"Existing": "CIR-009"})
    assert result["Existing"] == "CIR-009"
    assert result["New"] == "CIR-010"
    assert len(set(result.values())) == 2


def test_planner_ts_render_preserves_executable_suffix_as_text() -> None:
    current = 'export const plannerData = [{"area":"Old","macroThemes":[]}];\nexport function helper() { return "]"; }\n'
    catalog = [{"area": "Cirurgia", "macroThemes": []}]
    rendered = render_planner_ts(catalog, current)
    assert '"area": "Cirurgia"' in rendered
    assert 'export function helper() { return "]"; }' in rendered


def test_repository_taxonomy_artifacts_are_in_sync() -> None:
    artifacts = compile_artifacts()
    assert all(path.read_text(encoding="utf-8") == content for path, content in artifacts.items())
    compiled_map = json.loads(artifacts[SUBTEMA_MAP_PATH])
    assert len(compiled_map) == len(set(compiled_map.values())) == 275


def test_dry_run_does_not_mutate_database(tmp_path: Path) -> None:
    db_path = tmp_path / "content.db"
    map_path = tmp_path / "map.json"
    create_content_db(db_path)
    map_path.write_text(json.dumps({"Trauma Torácico": "CIR-001"}), encoding="utf-8")
    before = (db_path.stat().st_size, file_hash(db_path))
    plan = build_repair_plan(db_path, map_path)
    after = (db_path.stat().st_size, file_hash(db_path))
    assert before == after
    assert plan["mode"] == "dry_run"
    assert plan["summary"]["assign_subtema_ids"] == 2
    assert plan["summary"]["disable_critical_questions"] == 1
    assert plan["summary"]["synchronize_is_correct"] == 2
    assert set(plan["policy"]["never_automated"]) >= {"questions.stem", "alternatives.text", "explanations.explanation_text"}


def test_apply_uses_backup_transaction_and_only_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "content.db"
    map_path = tmp_path / "map.json"
    backup_dir = tmp_path / "backups"
    create_content_db(db_path)
    map_path.write_text(json.dumps({"Trauma Torácico": "CIR-001"}), encoding="utf-8")
    plan = build_repair_plan(db_path, map_path)
    result = apply_repair_plan(db_path, plan, backup_dir)
    backup_path = Path(result["backup"])
    assert backup_path.is_file()
    with sqlite3.connect(backup_path) as backup:
        assert backup.execute("SELECT stem, subtema_id FROM questions WHERE id=2").fetchone() == ("", None)
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT stem, subtema, subtema_id, missing_alts, status FROM questions WHERE id=2").fetchone() == ("", "Trauma Torácico", "CIR-001", 1, "quarantined")
        assert db.execute("SELECT explanation_text FROM explanations WHERE question_id=1").fetchone()[0] == "Curta"
        assert db.execute("SELECT letter,is_correct FROM alternatives WHERE question_id=1 ORDER BY letter").fetchall() == [("A", 1), ("B", 0), ("C", 0), ("D", 0)]
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_cli_refuses_apply_without_backup(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "scripts" / "content_repair.py"
    result = subprocess.run([sys.executable, str(script), "--db", str(tmp_path / "missing.db"), "--apply"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "--apply requires --backup-dir" in result.stderr
