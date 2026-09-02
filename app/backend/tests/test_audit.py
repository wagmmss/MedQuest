from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit.connection import get_readonly_connection
from scripts.audit.coverage import check_coverage
from scripts.audit.duplication import check_duplication
from scripts.audit.encoding import check_encoding
from scripts.audit.explanations import check_explanations
from scripts.audit.integrity import check_integrity
from scripts.audit.taxonomy import (
    check_taxonomy,
    load_canonical_safely,
    load_planner_ts_safely,
)
from scripts.validate import audit_database

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
VALIDATE = SCRIPTS_DIR / "validate.py"


def create_database(path: Path, *, with_is_correct: bool = True, optional_explanation_columns: bool = True) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    is_correct = ", is_correct INTEGER" if with_is_correct else ""
    explanation_optional = ", generated_at TEXT, reviewed_at TEXT" if optional_explanation_columns else ""
    db.executescript(f"""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY, stem TEXT, correct_letter TEXT,
            missing_alts INTEGER DEFAULT 0, area TEXT, subtema TEXT,
            institution_code TEXT, year INTEGER, source_file TEXT, source_number TEXT
        );
        CREATE TABLE alternatives (
            id INTEGER PRIMARY KEY, question_id INTEGER, letter TEXT, text TEXT{is_correct}
        );
        CREATE TABLE explanations (
            question_id INTEGER PRIMARY KEY, explanation_text TEXT{explanation_optional}
        );
        CREATE TABLE question_images (
            id INTEGER PRIMARY KEY, question_id INTEGER
        );
    """)
    return db


def insert_question(db: sqlite3.Connection, qid: int, *, stem: str = "Valid stem", correct: str = "A", missing_alts: int = 0, institution: str = "USP", year: int = 2024, source_file: str | None = None, source_number: str | None = None, alt_count: int = 4, with_is_correct: bool = True) -> None:
    db.execute("INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (qid, stem, correct, missing_alts, "Cirurgia", "Trauma Torácico", institution, year, source_file, source_number))
    for index, letter in enumerate("ABCDE"[:alt_count], start=1):
        if with_is_correct:
            db.execute("INSERT INTO alternatives(question_id,letter,text,is_correct) VALUES (?,?,?,?)", (qid, letter, f"alternative {index}", int(letter == correct)))
        else:
            db.execute("INSERT INTO alternatives(question_id,letter,text) VALUES (?,?,?)", (qid, letter, f"alternative {index}"))


@pytest.fixture
def valid_db(tmp_path: Path) -> Path:
    path = tmp_path / "valid.db"
    db = create_database(path)
    insert_question(db, 1)
    db.execute("INSERT INTO explanations(question_id, explanation_text) VALUES (1, ?)", ("A alternativa A é correta porque apresenta fundamentação clínica suficiente.",))
    db.commit()
    db.close()
    return path


def test_readonly_rejects_insert_update_and_pragmas(valid_db: Path) -> None:
    db = get_readonly_connection(valid_db)
    assert db.execute("PRAGMA query_only").fetchone()[0] == 1
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.execute("INSERT INTO questions(id) VALUES (99)")
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.execute("UPDATE questions SET stem=stem WHERE id=1")
    db.close()


def test_optional_schema_columns_are_supported(tmp_path: Path) -> None:
    path = tmp_path / "optional.db"
    db = create_database(path, with_is_correct=False, optional_explanation_columns=False)
    insert_question(db, 1, with_is_correct=False)
    db.commit(); db.close()
    ro = get_readonly_connection(path)
    assert check_integrity(ro)["schema"]["alternatives_is_correct_present"] is False
    assert len(check_explanations(ro)["schema_warnings"]) == 2
    ro.close()


def test_integrity_strict_failures_and_missing_alts_warning(tmp_path: Path) -> None:
    path = tmp_path / "integrity.db"
    db = create_database(path)
    insert_question(db, 1, stem="", correct="Z", alt_count=2)
    insert_question(db, 2, missing_alts=1)
    insert_question(db, 3, correct="E", alt_count=4)
    db.execute("UPDATE alternatives SET text='' WHERE question_id=1 AND letter='A'")
    db.execute("INSERT INTO alternatives(question_id,letter,text,is_correct) VALUES (1,'A','duplicate',0)")
    db.commit(); db.close()
    ro = get_readonly_connection(path)
    result = check_integrity(ro)
    assert result["critical_failures"]["empty_statements"] == [1]
    assert result["critical_failures"]["invalid_correct_letters"][0]["question_id"] == 1
    assert result["critical_failures"]["empty_alternatives"][0]["question_id"] == 1
    assert result["critical_failures"]["duplicate_alternative_letters"][0]["letters"] == ["A"]
    assert result["critical_failures"]["answer_without_alternative"][0]["question_id"] == 3
    assert result["critical_failures"]["missing_alts_0_incomplete"][0]["question_id"] == 1
    assert result["warnings"]["missing_alts_1_complete"] == [2]
    ro.close()


def test_validate_can_block_publication_on_warnings(valid_db: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATE), "--db", str(valid_db), "--fail-on-warnings"],
        capture_output=True,
        text=True,
    )
    # The fixture has taxonomy warnings because it is intentionally minimal;
    # this verifies the publication-mode gate without mutating the database.
    assert result.returncode == 1
    assert "Warnings encontrados" in result.stderr


def test_all_orphan_types_and_duplicate_origin_are_critical(tmp_path: Path) -> None:
    path = tmp_path / "orphans.db"
    db = create_database(path)
    insert_question(db, 1, source_file="exam.pdf", source_number="1")
    insert_question(db, 2, source_file="exam.pdf", source_number="1")
    db.execute("INSERT INTO alternatives(question_id,letter,text,is_correct) VALUES (999,'A','orphan',0)")
    db.execute("INSERT INTO explanations(question_id,explanation_text) VALUES (998,'orphan')")
    db.execute("INSERT INTO question_images(id,question_id) VALUES (997,997)")
    db.commit(); db.close()
    ro = get_readonly_connection(path); result = check_integrity(ro); ro.close()
    assert result["critical_failures"]["orphans"] == {"alternatives": [9], "explanations": [998], "question_images": [997]}
    assert result["critical_failures"]["duplicate_source_file_number"][0]["question_ids"] == [1, 2]


def test_duplicate_categories_sha256_context_and_exclusivity(tmp_path: Path) -> None:
    path = tmp_path / "dups.db"; db = create_database(path)
    insert_question(db, 1, stem="Same stem", institution="USP", year=2024)
    insert_question(db, 2, stem="Same stem\u200b", institution="USP", year=2024)
    insert_question(db, 3, stem="Other, STEM!", institution="UNIFESP", year=2023)
    insert_question(db, 4, stem="other stem", institution="USP", year=2024)
    db.commit(); db.close()
    ro = get_readonly_connection(path); result = check_duplication(ro); ro.close()
    assert result["literal_exact"]["groups_count"] == 1
    assert result["normalized_exact"]["groups_count"] == 1
    literal_ids = {q["id"] for groups in result["literal_exact"]["contexts"].values() for group in groups for q in group["questions"]}
    normalized_ids = {q["id"] for groups in result["normalized_exact"]["contexts"].values() for group in groups for q in group["questions"]}
    assert literal_ids.isdisjoint(normalized_ids)
    assert all(len(group["sha256"]) == 64 for category in ("literal_exact", "normalized_exact") for groups in result[category]["contexts"].values() for group in groups)
    assert result["probable_duplicate"]["status"] == "not_executed"


def test_canonical_parser_literal_eval_never_executes(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    safe = tmp_path / "safe.py"
    safe.write_text("CANONICAL = {'Cirurgia': ['Trauma']}\n", encoding="utf-8")
    assert load_canonical_safely(safe)["status"] == "verified"
    unsafe = tmp_path / "unsafe.py"
    unsafe.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\nCANONICAL = dict()\n", encoding="utf-8")
    assert load_canonical_safely(unsafe)["status"] == "unverified"
    assert not marker.exists()


def test_typescript_balanced_scanner_handles_strings_and_escapes(tmp_path: Path) -> None:
    path = tmp_path / "plannerData.ts"
    path.write_text('export const plannerData = [{"area":"A ] } \\\" ok","macroThemes":[{"dbSubtemas":["S"]}]}];\nexport function x() {}', encoding="utf-8")
    result = load_planner_ts_safely(path)
    assert result["status"] == "verified"
    assert result["data"][0]["macroThemes"][0]["dbSubtemas"] == ["S"]


def test_typescript_non_json_is_unverified(tmp_path: Path) -> None:
    path = tmp_path / "plannerData.ts"
    path.write_text("export const plannerData = [{area: 'A'}];", encoding="utf-8")
    result = load_planner_ts_safely(path)
    assert result["status"] == "unverified"
    assert result["warnings"]


def test_taxonomy_compares_all_four_real_sources(valid_db: Path) -> None:
    ro = get_readonly_connection(valid_db); result = check_taxonomy(ro, SCRIPTS_DIR); ro.close()
    assert set(result["sources"]) == {"taxonomy_json", "canonical_subtemas_py", "plannerData_json", "plannerData_ts"}
    assert all(source["status"] == "verified" for source in result["sources"].values())
    assert result["sources"]["plannerData_json"]["consumers"] == ["backend/scripts/planner.py"]
    assert result["sources"]["plannerData_ts"]["consumers"] == ["frontend PlannerClient.tsx"]


def test_coverage_has_eight_distributions_thresholds_and_truncation(tmp_path: Path) -> None:
    path = tmp_path / "coverage.db"; db = create_database(path)
    for qid in range(1, 7):
        insert_question(db, qid, stem=f"stem {qid}", institution=f"I{qid}", year=2020 + qid)
        db.execute("UPDATE questions SET subtema=? WHERE id=?", (f"S{qid}", qid))
    db.commit(); db.close()
    ro = get_readonly_connection(path); result = check_coverage(ro, SCRIPTS_DIR, max_details=2); ro.close()
    assert len(result["distributions"]) == 8
    assert result["distributions"]["institution"] == {**result["distributions"]["institution"], "total_items": 6, "returned_items": 2, "truncated": True}
    assert set(("under_5_questions", "under_10_questions", "under_20_questions")).issubset(result["gaps"])


def test_human_queue_is_unique_exclusive_and_has_reasons(tmp_path: Path) -> None:
    path = tmp_path / "queue.db"; db = create_database(path)
    insert_question(db, 1); insert_question(db, 2); insert_question(db, 3)
    db.execute("INSERT INTO explanations(question_id,explanation_text) VALUES (1,'TODO...')")
    db.execute("INSERT INTO explanations(question_id,explanation_text) VALUES (2,'Texto curto')")
    db.commit(); db.close()
    ro = get_readonly_connection(path); result = check_explanations(ro, 50); ro.close()
    queue = result["human_review_queue"]
    bucket_ids = [item["question_id"] for name in ("high_priority", "medium_priority", "low_priority") for item in queue[name]]
    assert len(bucket_ids) == len(set(bucket_ids)) == len(queue["all"])
    assert all(item["reasons"] for item in queue["all"])
    assert {"residual_marker", "potentially_truncated", "too_short"}.issubset(queue["all"][0]["reasons"])


def test_encoding_categories(valid_db: Path) -> None:
    db = sqlite3.connect(valid_db)
    db.execute("UPDATE questions SET stem='Clínica MÃ©dica\u200b' WHERE id=1")
    db.commit(); db.close()
    ro = get_readonly_connection(valid_db); result = check_encoding(ro); ro.close()
    assert result["probable_mojibake"][0]["id"] == 1
    assert result["zero_width_character"][0]["id"] == 1


def test_json_contract_and_determinism(valid_db: Path) -> None:
    first = audit_database(valid_db, max_details=1, generated_at="one")
    second = audit_database(valid_db, max_details=1, generated_at="two")
    assert "summary" in first and "warnings" in first
    assert len(first["coverage"]["distributions"]) == 8
    first.pop("generated_at"); second.pop("generated_at")
    assert first == second


def test_cli_strict_zero_and_one_without_traceback(valid_db: Path, tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    good = subprocess.run([sys.executable, str(VALIDATE), "--db", str(valid_db), "--strict", "--max-details", "1"], capture_output=True, text=True, encoding="utf-8", env=env)
    assert good.returncode == 0
    assert "Traceback" not in good.stderr
    db = sqlite3.connect(valid_db)
    insert_question(db, 2, correct="Z", alt_count=2)
    db.commit(); db.close()
    output = tmp_path / "strict.json"
    bad = subprocess.run([sys.executable, str(VALIDATE), "--db", str(valid_db), "--strict", "--output", str(output)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert bad.returncode == 1
    assert "Falhas críticas" in bad.stderr
    assert "Traceback" not in bad.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["critical_failure_records"] > 0
