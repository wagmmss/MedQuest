"""Plan or apply deterministic Sprint C2 content repairs.

Dry-run is the default. ``--apply`` requires a backup directory and performs a
single SQLite transaction. The script never writes stems, alternative text,
explanations, medical references, areas or subtema labels; those require human
editorial/medical review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    from audit.connection import get_readonly_connection
    from audit.explanations import check_explanations
    from audit.integrity import VALID_LETTERS, check_integrity
except ModuleNotFoundError:
    from scripts.audit.connection import get_readonly_connection
    from scripts.audit.explanations import check_explanations
    from scripts.audit.integrity import VALID_LETTERS, check_integrity

DEFAULT_DB = Path(__file__).resolve().parents[1] / "medquest.db"
DEFAULT_MAP = Path(__file__).resolve().parents[1] / "data" / "subtema_map.json"


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in db.execute(f"PRAGMA table_info({table})")}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _critical_question_ids(critical: dict) -> list[int]:
    ids = set(critical["empty_statements"])
    ids.update(item["question_id"] for item in critical["empty_alternatives"])
    ids.update(item["question_id"] for item in critical["invalid_correct_letters"])
    ids.update(item["question_id"] for item in critical["answer_without_alternative"])
    ids.update(item["question_id"] for item in critical["duplicate_alternative_letters"])
    ids.update(item["question_id"] for item in critical["missing_alts_0_incomplete"])
    return sorted(ids)


def build_repair_plan(db_path: Path, map_path: Path = DEFAULT_MAP) -> dict:
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    db = get_readonly_connection(db_path)
    try:
        qcols = _columns(db, "questions")
        acols = _columns(db, "alternatives")
        integrity = check_integrity(db)
        explanations = check_explanations(db)
        critical_ids = _critical_question_ids(integrity["critical_failures"])

        disable_ids = []
        quarantine_ids = []
        if critical_ids:
            placeholders = ",".join("?" for _ in critical_ids)
            selected = db.execute(
                f"SELECT id, missing_alts" + (", status" if "status" in qcols else "")
                + f" FROM questions WHERE id IN ({placeholders}) ORDER BY id",
                critical_ids,
            ).fetchall()
            disable_ids = [row["id"] for row in selected if row["missing_alts"] != 1]
            quarantine_ids = [row["id"] for row in selected if "status" in qcols and row["status"] != "quarantined"]

        subtema_id_updates = []
        if "subtema_id" in qcols:
            for row in db.execute("SELECT id, subtema, subtema_id FROM questions WHERE trim(COALESCE(subtema, '')) != '' ORDER BY id"):
                expected = mapping.get(row["subtema"])
                if expected and row["subtema_id"] != expected:
                    subtema_id_updates.append({"question_id": row["id"], "subtema_id": expected})

        is_correct_updates = []
        if "is_correct" in acols:
            query = """
                SELECT a.id, a.is_correct, upper(trim(a.letter)) AS letter,
                       upper(trim(q.correct_letter)) AS correct_letter
                FROM alternatives a JOIN questions q ON q.id=a.question_id
                WHERE EXISTS (
                    SELECT 1 FROM alternatives match
                    WHERE match.question_id=q.id
                      AND upper(trim(match.letter))=upper(trim(q.correct_letter))
                )
                ORDER BY a.id
            """
            for row in db.execute(query):
                expected = int(row["correct_letter"] in VALID_LETTERS and row["letter"] == row["correct_letter"])
                if row["is_correct"] != expected:
                    is_correct_updates.append({"alternative_id": row["id"], "is_correct": expected})

        review_ids = [item["question_id"] for item in explanations["human_review_queue"]["all"]]
        editorial_review_ids = []
        if "editorial_status" in qcols and review_ids:
            for start in range(0, len(review_ids), 500):
                chunk = review_ids[start:start + 500]
                placeholders = ",".join("?" for _ in chunk)
                editorial_review_ids.extend(
                    row["id"] for row in db.execute(
                        f"SELECT id FROM questions WHERE id IN ({placeholders}) AND COALESCE(editorial_status, '') != 'needs_human_review' ORDER BY id",
                        chunk,
                    )
                )

        unmapped = db.execute(
            "SELECT COUNT(*) FROM questions WHERE trim(COALESCE(subtema, '')) != '' AND subtema NOT IN ("
            + ",".join("?" for _ in mapping) + ")",
            list(mapping),
        ).fetchone()[0]
    finally:
        db.close()

    operations = {
        "disable_critical_questions": disable_ids,
        "quarantine_critical_questions": quarantine_ids,
        "assign_subtema_ids": subtema_id_updates,
        "synchronize_is_correct": is_correct_updates,
        "mark_explanations_for_human_review": sorted(editorial_review_ids),
    }
    return {
        "schema_version": "2.0.0",
        "database": str(db_path.resolve()),
        "mode": "dry_run",
        "policy": {
            "automated_fields": ["questions.missing_alts", "questions.status", "questions.subtema_id", "questions.editorial_status", "alternatives.is_correct"],
            "never_automated": ["questions.stem", "alternatives.text", "explanations.explanation_text", "questions.medical_references", "questions.area", "questions.subtema"],
            "medical_review": "human_required",
        },
        "summary": {name: len(items) for name, items in operations.items()} | {
            "critical_questions": len(critical_ids),
            "unmapped_database_subtemas": int(unmapped),
        },
        "operations": operations,
        "warnings": [
            "Empty or medically questionable content is quarantined/queued, never generated or rewritten automatically.",
            "Applying this plan changes operational metadata only and requires a verified backup.",
        ],
    }


def apply_repair_plan(db_path: Path, plan: dict, backup_dir: Path) -> dict:
    backup_dir.mkdir(parents=True, exist_ok=True)
    before = {"size": db_path.stat().st_size, "sha256": _sha256(db_path)}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{db_path.stem}-pre-c2-{stamp}.db"
    if backup_path.exists():
        raise FileExistsError(backup_path)

    db = sqlite3.connect(db_path)
    try:
        with sqlite3.connect(backup_path) as backup:
            db.backup(backup)
        backup_hash = _sha256(backup_path)
        db.execute("BEGIN IMMEDIATE")
        operations = plan["operations"]
        db.executemany("UPDATE questions SET missing_alts=1 WHERE id=?", ((qid,) for qid in operations["disable_critical_questions"]))
        db.executemany("UPDATE questions SET status='quarantined' WHERE id=?", ((qid,) for qid in operations["quarantine_critical_questions"]))
        db.executemany("UPDATE questions SET subtema_id=? WHERE id=?", ((item["subtema_id"], item["question_id"]) for item in operations["assign_subtema_ids"]))
        db.executemany("UPDATE alternatives SET is_correct=? WHERE id=?", ((item["is_correct"], item["alternative_id"]) for item in operations["synchronize_is_correct"]))
        db.executemany("UPDATE questions SET editorial_status='needs_human_review' WHERE id=?", ((qid,) for qid in operations["mark_explanations_for_human_review"]))
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("integrity_check failed; rolling back")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    result = {
        "backup": str(backup_path.resolve()),
        "backup_sha256": backup_hash,
        "before": before,
        "after": {"size": db_path.stat().st_size, "sha256": _sha256(db_path)},
        "applied": plan["summary"],
    }
    (backup_dir / f"{backup_path.stem}.manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def render_markdown(plan: dict) -> str:
    summary = plan["summary"]
    lines = [
        "# Sprint C2 — Plano de remediação de conteúdo",
        "",
        f"**Modo:** `{plan['mode']}`",
        f"**Banco analisado:** {plan['database']}",
        "",
        "## Escopo automatizado",
        "",
        "A C2 automatiza somente metadados técnicos determinísticos. Enunciados, alternativas, explicações, referências médicas e rótulos taxonômicos não são reescritos.",
        "",
        f"- Questões críticas únicas: {summary['critical_questions']}",
        f"- Questões a desabilitar por falha estrutural: {summary['disable_critical_questions']}",
        f"- Questões a colocar em quarentena: {summary['quarantine_critical_questions']}",
        f"- IDs canônicos de subtema a atribuir: {summary['assign_subtema_ids']}",
        f"- Flags redundantes `is_correct` a sincronizar: {summary['synchronize_is_correct']}",
        f"- Questões a marcar para revisão humana: {summary['mark_explanations_for_human_review']}",
        f"- Subtemas do banco sem ID no catálogo: {summary['unmapped_database_subtemas']}",
        "",
        "## Política de segurança editorial",
        "",
        "- A execução padrão é dry-run.",
        "- `--apply` exige diretório de backup e uma transação SQLite única.",
        "- Conteúdo médico nunca é gerado ou corrigido automaticamente.",
        "- Explicações sinalizadas recebem apenas `needs_human_review`.",
        "- Falhas estruturais são desabilitadas/quarentenadas; os textos originais são preservados.",
        "",
        "## Campos que nunca são automatizados",
        "",
    ]
    lines.extend(f"- `{field}`" for field in plan["policy"]["never_automated"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in plan["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--md", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    if args.apply and args.backup_dir is None:
        parser.error("--apply requires --backup-dir")
    plan = build_repair_plan(args.db, args.map)
    if args.apply:
        plan["mode"] = "apply"
        plan["application"] = apply_repair_plan(args.db, plan, args.backup_dir)
    payload = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(render_markdown(plan), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
