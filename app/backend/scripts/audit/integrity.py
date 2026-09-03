"""Structural integrity checks for the MedQuest content database."""
from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

from .connection import rows, scalar

VALID_LETTERS = {"A", "B", "C", "D", "E"}


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in db.execute(f"PRAGMA table_info({table})")}


def _table_exists(db: sqlite3.Connection, table: str) -> bool:
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _clean_letter(value: object) -> str:
    return str(value or "").strip().upper()


def check_integrity(db: sqlite3.Connection) -> dict:
    qcols = _columns(db, "questions")
    acols = _columns(db, "alternatives")
    missing_columns = {
        "questions": sorted({"id", "stem", "correct_letter", "missing_alts"} - qcols),
        "alternatives": sorted({"id", "question_id", "letter", "text"} - acols),
    }
    if any(missing_columns.values()):
        raise ValueError(f"Schema obrigatório ausente: {missing_columns}")

    optional_q = [name for name in ("area", "subtema", "source_file", "source_number") if name in qcols]
    questions = rows(db, "SELECT id, stem, correct_letter, missing_alts" + (", " + ", ".join(optional_q) if optional_q else "") + " FROM questions ORDER BY id")
    alternatives = rows(db, "SELECT id, question_id, letter, text" + (", is_correct" if "is_correct" in acols else "") + " FROM alternatives ORDER BY question_id, id")

    question_ids = {q["id"] for q in questions}
    alts_by_question: dict[int, list[dict]] = defaultdict(list)
    orphan_alternatives: list[int] = []
    empty_alternatives: list[dict] = []
    for alt in alternatives:
        if alt["question_id"] not in question_ids:
            orphan_alternatives.append(alt["id"])
            continue
        alts_by_question[alt["question_id"]].append(alt)
        if not str(alt["text"] or "").strip():
            empty_alternatives.append({"alternative_id": alt["id"], "question_id": alt["question_id"]})

    empty_statements: list[int] = []
    invalid_correct_letters: list[dict] = []
    answer_without_alternative: list[dict] = []
    duplicate_letters: list[dict] = []
    missing_alts_0_incomplete: list[dict] = []
    missing_alts_1_complete: list[int] = []
    is_correct_mismatches: list[dict] = []
    distribution: Counter[int] = Counter()

    for question in questions:
        qid = question["id"]
        if not str(question["stem"] or "").strip():
            empty_statements.append(qid)
        correct = _clean_letter(question["correct_letter"])
        valid_candidates = {c.strip() for c in correct.split(",") if c.strip()}
        is_anulada = (correct == "ANULADA")
        if not (is_anulada or (valid_candidates and valid_candidates.issubset(VALID_LETTERS))):
            invalid_correct_letters.append({"question_id": qid, "value": question["correct_letter"]})

        alts = alts_by_question.get(qid, [])
        distribution[len(alts)] += 1
        letters = [_clean_letter(alt["letter"]) for alt in alts]
        duplicated = sorted(letter for letter, count in Counter(letters).items() if count > 1)
        if duplicated:
            duplicate_letters.append({"question_id": qid, "letters": duplicated})
        if valid_candidates and valid_candidates.issubset(VALID_LETTERS):
            if not any(cand in letters for cand in valid_candidates):
                answer_without_alternative.append({"question_id": qid, "correct_letter": correct, "available": sorted(letters)})

        is_discursive = len(alts) <= 1
        if is_discursive:
            structurally_complete = all(str(alt["text"] or "").strip() for alt in alts)
        else:
            structurally_complete = (
                len(alts) in (4, 5)
                and len(set(letters)) == len(letters)
                and all(letter in VALID_LETTERS for letter in letters)
                and all(str(alt["text"] or "").strip() for alt in alts)
                and (is_anulada or any(cand in letters for cand in valid_candidates))
            )
        if question["missing_alts"] == 0 and not structurally_complete:
            missing_alts_0_incomplete.append({"question_id": qid, "alternatives": len(alts), "letters": letters})
        elif question["missing_alts"] == 1 and structurally_complete and not is_discursive:
            missing_alts_1_complete.append(qid)

        if "is_correct" in acols:
            marked = sorted(_clean_letter(alt["letter"]) for alt in alts if bool(alt.get("is_correct")))
            if is_anulada:
                expected = marked
            else:
                expected = sorted(cand for cand in valid_candidates if cand in VALID_LETTERS)
            if marked != expected:
                is_correct_mismatches.append({"question_id": qid, "correct_letter": correct, "marked": marked})

    duplicate_sources: list[dict] = []
    if {"source_file", "source_number"}.issubset(qcols):
        duplicate_sources = rows(db, """
            SELECT source_file, source_number, COUNT(*) AS count, GROUP_CONCAT(id) AS question_ids
            FROM questions
            WHERE trim(COALESCE(source_file, '')) != ''
              AND trim(COALESCE(CAST(source_number AS TEXT), '')) != ''
            GROUP BY source_file, source_number HAVING COUNT(*) > 1
            ORDER BY source_file, source_number
        """)
        for item in duplicate_sources:
            item["question_ids"] = sorted(int(value) for value in item["question_ids"].split(","))

    orphans: dict[str, list[int]] = {"alternatives": sorted(orphan_alternatives)}
    for table, select_id in (("explanations", "question_id"), ("question_images", "id")):
        if not _table_exists(db, table):
            orphans[table] = []
            continue
        orphans[table] = [item["record_id"] for item in rows(db, f"SELECT {select_id} AS record_id FROM {table} WHERE question_id NOT IN (SELECT id FROM questions) ORDER BY record_id")]

    missing_metadata = {}
    for column in ("area", "subtema"):
        missing_metadata[column] = scalar(db, f"SELECT COUNT(*) FROM questions WHERE trim(COALESCE({column}, '')) = ''") if column in qcols else None

    critical_failures = {
        "empty_statements": sorted(empty_statements),
        "empty_alternatives": sorted(empty_alternatives, key=lambda item: item["alternative_id"]),
        "invalid_correct_letters": sorted(invalid_correct_letters, key=lambda item: item["question_id"]),
        "answer_without_alternative": sorted(answer_without_alternative, key=lambda item: item["question_id"]),
        "duplicate_alternative_letters": sorted(duplicate_letters, key=lambda item: item["question_id"]),
        "orphans": orphans,
        "missing_alts_0_incomplete": sorted(missing_alts_0_incomplete, key=lambda item: item["question_id"]),
        "duplicate_source_file_number": duplicate_sources,
    }
    return {
        "total": len(questions),
        "usable": sum(q["missing_alts"] == 0 for q in questions),
        "not_usable": sum(q["missing_alts"] != 0 for q in questions),
        "missing_metadata": missing_metadata,
        "alternatives_distribution": [{"alternatives": count, "questions": distribution[count]} for count in sorted(distribution)],
        "critical_failures": critical_failures,
        "warnings": {
            "missing_alts_1_complete": sorted(missing_alts_1_complete),
            "is_correct_mismatches": sorted(is_correct_mismatches, key=lambda item: item["question_id"]),
        },
        "schema": {"optional_question_columns_present": sorted(optional_q), "alternatives_is_correct_present": "is_correct" in acols},
    }
