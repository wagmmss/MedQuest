"""Auditoria read-only de integridade e cobertura do banco local do MedQuest."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


DEFAULT_DB = Path(__file__).resolve().parents[1] / "medquest.db"
PLANNER_CATALOG = Path(__file__).with_name("plannerData.json")


def scalar(db: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(db.execute(sql, params).fetchone()[0] or 0)


def rows(db: sqlite3.Connection, sql: str) -> list[dict]:
    return [dict(row) for row in db.execute(sql).fetchall()]


def audit(db_path: Path) -> dict:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        question_columns = {
            row[1] for row in db.execute("PRAGMA table_info(questions)").fetchall()
        }
        db_subtemas = rows(db, """
            SELECT subtema, COUNT(*) AS questions FROM questions
            WHERE trim(COALESCE(subtema, '')) != ''
            GROUP BY subtema ORDER BY questions DESC
        """)
        with PLANNER_CATALOG.open(encoding="utf-8") as catalog_file:
            planner_catalog = json.load(catalog_file)
        catalog_subtemas = {
            subtema
            for area_group in planner_catalog
            for macro in area_group.get("macroThemes", [])
            for subtema in macro.get("dbSubtemas", [])
        }
        db_subtema_names = {item["subtema"] for item in db_subtemas}
        mapped_question_count = sum(
            item["questions"] for item in db_subtemas
            if item["subtema"] in catalog_subtemas
        )
        unmapped_question_count = sum(
            item["questions"] for item in db_subtemas
            if item["subtema"] not in catalog_subtemas
        )

        result = {
            "database": str(db_path),
            "questions": {
                "total": scalar(db, "SELECT COUNT(*) FROM questions"),
                "usable": scalar(db, "SELECT COUNT(*) FROM questions WHERE missing_alts = 0"),
                "missing_alternatives": scalar(db, "SELECT COUNT(*) FROM questions WHERE missing_alts = 1"),
                "without_area": scalar(db, "SELECT COUNT(*) FROM questions WHERE area IS NULL OR trim(area) = ''"),
                "without_subtema": scalar(db, "SELECT COUNT(*) FROM questions WHERE subtema IS NULL OR trim(subtema) = ''"),
                "without_valid_answer": scalar(db, "SELECT COUNT(*) FROM questions WHERE upper(correct_letter) NOT IN ('A','B','C','D','E')"),
                "duplicate_source_numbers": scalar(db, """
                    SELECT COUNT(*) FROM (
                        SELECT source_file, source_number FROM questions
                        GROUP BY source_file, source_number HAVING COUNT(*) > 1
                    )
                """),
            },
            "content": {
                "explanations": scalar(db, "SELECT COUNT(*) FROM explanations WHERE trim(COALESCE(explanation_text, '')) != ''"),
                "usable_without_explanation": scalar(db, """
                    SELECT COUNT(*) FROM questions q
                    LEFT JOIN explanations e ON e.question_id = q.id
                    WHERE q.missing_alts = 0 AND trim(COALESCE(e.explanation_text, '')) = ''
                """),
                "images": scalar(db, "SELECT COUNT(*) FROM question_images"),
                "questions_with_4_or_5_options": scalar(db, """
                    SELECT COUNT(*) FROM (
                        SELECT question_id FROM alternatives
                        GROUP BY question_id HAVING COUNT(*) IN (4, 5)
                    )
                """),
                "duplicate_alternative_letters": scalar(db, """
                    SELECT COUNT(*) FROM (
                        SELECT question_id, upper(letter) FROM alternatives
                        GROUP BY question_id, upper(letter) HAVING COUNT(*) > 1
                    )
                """),
            },
            "coverage": {
                "areas": rows(db, "SELECT area, COUNT(*) AS questions FROM questions GROUP BY area ORDER BY questions DESC"),
                "institutions": rows(db, "SELECT institution_code, COUNT(*) AS questions FROM questions GROUP BY institution_code ORDER BY questions DESC"),
                "years": rows(db, "SELECT year, COUNT(*) AS questions FROM questions GROUP BY year ORDER BY year DESC"),
                "usp_sp_2026_by_area": rows(db, """
                    SELECT area, COUNT(*) AS questions FROM questions
                    WHERE institution_code = 'USP-SP' AND year = 2026
                    GROUP BY area ORDER BY questions DESC
                """),
                "distinct_subtemas": scalar(db, "SELECT COUNT(DISTINCT subtema) FROM questions WHERE trim(COALESCE(subtema, '')) != ''"),
                "subtemas_with_fewer_than_10_questions": [
                    item for item in db_subtemas if item["questions"] < 10
                ],
                "planner_catalog": {
                    "catalog_subtemas": len(catalog_subtemas),
                    "database_subtemas_mapped": len(db_subtema_names & catalog_subtemas),
                    "database_questions_mapped": mapped_question_count,
                    "database_questions_unmapped": unmapped_question_count,
                    "database_subtemas_unmapped": [
                        item for item in db_subtemas if item["subtema"] not in catalog_subtemas
                    ],
                    "catalog_subtemas_without_questions": sorted(catalog_subtemas - db_subtema_names),
                },
            },
        }

        if "specialty" in question_columns:
            result["questions"]["without_specialty"] = scalar(
                db, "SELECT COUNT(*) FROM questions WHERE specialty IS NULL OR trim(specialty) = ''"
            )
        if "is_verified" in question_columns:
            result["content"]["verified_questions"] = scalar(
                db, "SELECT COUNT(*) FROM questions WHERE is_verified = 1"
            )
        if "medical_references" in question_columns:
            result["content"]["questions_with_medical_references"] = scalar(
                db, "SELECT COUNT(*) FROM questions WHERE trim(COALESCE(medical_references, '')) != ''"
            )

        try:
            result["content"]["fts_rows"] = scalar(db, "SELECT COUNT(*) FROM questions_fts")
        except sqlite3.OperationalError:
            result["content"]["fts_rows"] = None
        return result
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db", nargs="?", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"Banco não encontrado: {args.db}")
    print(json.dumps(audit(args.db.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
