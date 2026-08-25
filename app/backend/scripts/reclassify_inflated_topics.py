"""Reclassify the three known fallback subtemas using the verified topic map.

The script is deliberately dry-run by default.  With ``--apply`` it creates a
SQLite backup, writes an auditable proposal per question, and updates the
published area/subtema values in one transaction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
DATABASE = ROOT / "app" / "backend" / "medquest.db"
TAXONOMY = ROOT / "canonical_taxonomy_170.json"
TOPIC_MAP = ROOT / "full_topic_map.json"
BACKUP_DIR = ROOT / "backups" / "taxonomy-reclassification"
REPORT_DIR = ROOT / "docs" / "audits"

FALLBACK_SUBTEMAS = (
    "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)",
    "Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose",
    "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
)

# ``full_topic_map.json`` also serves a newer, 187-theme taxonomy.  These
# aliases keep the present operation strictly inside the requested 170-theme
# taxonomy.  The three palliative-care source labels have no dedicated theme
# among the 170, so they remain under the closest canonical geriatrics theme.
CANONICAL_170_OVERRIDES = {
    "Cuidados Paliativos (PED)": (
        "Clínica Médica",
        "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
    ),
    "Cuidados Paliativos - Oncologia (CM)": (
        "Clínica Médica",
        "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
    ),
    "Síndrome Hemolítico Urêmica (PED)": (
        "Pediatria",
        "Vasculites na Infância (Henoch-Schönlein e Kawasaki)",
    ),
    "Nefropatia membranosa (CM)": (
        "Clínica Médica",
        "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
    ),
}

# The source map includes a few pediatric destinations added after the
# 170-theme taxonomy.  The 170-theme equivalents live in Clínica Médica; this
# preserves the clinical subject rather than forcing a non-canonical label.
CANONICAL_170_DESTINATION_ALIASES = {
    ("Pediatria", "Pneumonias Comunitárias, Complicadas e Atípicas na Criança"): (
        "Clínica Médica",
        "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas",
    ),
    ("Pediatria", "Síndrome Nefrítica, Síndrome Nefrótica e Glomerulopatias na Infância"): (
        "Clínica Médica",
        "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
    ),
    ("Clínica Médica", "Glomerulopatias: Nefropatias Primárias e Secundárias no Adulto"): (
        "Clínica Médica",
        "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
    ),
    ("Pediatria", "Tuberculose na Infância e Teste Tuberculínico / PPD"): (
        "Clínica Médica",
        "Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo",
    ),
    ("Clínica Médica", "Meningites Infecciosas, Encefalites e Neuroinfecções"): (
        "Clínica Médica",
        "Meningites, Encefalites e Infecções do SNC",
    ),
    ("Pediatria", "Neonatologia: Prematuridade e Desconforto Respiratório"): (
        "Cirurgia",
        "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_valid_destinations() -> set[tuple[str, str]]:
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return {(area, theme) for area, themes in taxonomy.items() for theme in themes}


def planned_changes(connection: sqlite3.Connection, source_subtemas: tuple[str, ...]) -> list[dict]:
    topic_map = json.loads(TOPIC_MAP.read_text(encoding="utf-8"))
    valid_destinations = load_valid_destinations()
    placeholders = ", ".join("?" for _ in source_subtemas)
    rows = connection.execute(
        f"""
        SELECT id, area, subtema, topic
        FROM questions
        WHERE subtema IN ({placeholders})
        ORDER BY id
        """,
        source_subtemas,
    ).fetchall()

    plan: list[dict] = []
    for question_id, old_area, old_subtema, topic in rows:
        destination = topic_map.get(topic)
        if destination is None:
            raise ValueError(f"Questão {question_id} não tem destino para tema-fonte {topic!r}.")
        target = CANONICAL_170_OVERRIDES.get(topic, (destination["area"], destination["subtema"]))
        target = CANONICAL_170_DESTINATION_ALIASES.get(target, target)
        if target not in valid_destinations:
            raise ValueError(f"Questão {question_id} tem destino não canônico: {target!r}.")
        plan.append(
            {
                "question_id": question_id,
                "source_topic": topic,
                "old_area": old_area,
                "old_subtema": old_subtema,
                "new_area": target[0],
                "new_subtema": target[1],
                "changed": (old_area, old_subtema) != target,
            }
        )
    return plan


def report(plan: list[dict], run_id: str | None = None, backup: Path | None = None) -> dict:
    changed = [item for item in plan if item["changed"]]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_id": run_id,
        "backup": str(backup) if backup else None,
        "questions_examined": len(plan),
        "questions_reclassified": len(changed),
        "questions_retained": len(plan) - len(changed),
        "by_previous_subtema": dict(Counter(item["old_subtema"] for item in plan)),
        "by_destination": [
            {"area": area, "subtema": subtema, "questions": count}
            for (area, subtema), count in sorted(
                Counter((item["new_area"], item["new_subtema"]) for item in plan).items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "changes": changed,
    }


def apply_plan(connection: sqlite3.Connection, plan: list[dict], run_id: str) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    input_hash = hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            """
            INSERT INTO classification_runs
                (id, taxonomy_version, pipeline_version, input_hash, status, created_at, notes)
            VALUES (?, ?, ?, ?, 'completed', ?, ?)
            """,
            (
                run_id,
                "canonical_taxonomy_170.json",
                "topic-map-reclassification-v1",
                input_hash,
                now,
                "Reclassificação dos três subtemas-fallback inflados, com tema-fonte mapeado.",
            ),
        )
        for item in plan:
            confidence = 0.99 if item["changed"] else 1.0
            cursor = connection.execute(
                """
                INSERT INTO classification_proposals
                    (run_id, question_id, reviewer_role, decision, proposed_area,
                     proposed_subtema, confidence, evidence, alternatives_json, status, created_at)
                VALUES (?, ?, 'triage', 'classify', ?, ?, ?, ?, '[]', 'accepted', ?)
                """,
                (
                    run_id,
                    item["question_id"],
                    item["new_area"],
                    item["new_subtema"],
                    confidence,
                    f"Tema-fonte mapeado: {item['source_topic']}",
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO classification_reviews
                    (proposal_id, reviewer, decision, final_area, final_subtema, rationale, reviewed_at)
                VALUES (?, 'topic-map-reclassification', 'accept', ?, ?, ?, ?)
                """,
                (
                    cursor.lastrowid,
                    item["new_area"],
                    item["new_subtema"],
                    "Destino canônico definido pelo mapeamento do tema-fonte.",
                    now,
                ),
            )
            if item["changed"]:
                connection.execute(
                    "UPDATE questions SET area = ?, subtema = ? WHERE id = ?",
                    (item["new_area"], item["new_subtema"], item["question_id"]),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplica o plano após criar backup.")
    parser.add_argument(
        "--subtema",
        action="append",
        dest="subtemas",
        help="Subtema-fonte a reclassificar; pode ser informado mais de uma vez.",
    )
    args = parser.parse_args()

    connection = sqlite3.connect(DATABASE)
    try:
        source_subtemas = tuple(args.subtemas or FALLBACK_SUBTEMAS)
        plan = planned_changes(connection, source_subtemas)
        summary = report(plan)
        print(json.dumps({key: value for key, value in summary.items() if key != "changes"}, ensure_ascii=False, indent=2))
        if not args.apply:
            return 0

        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / f"medquest-pre-inflated-topics-{timestamp}.db"
        with sqlite3.connect(backup) as destination:
            connection.backup(destination)
        if not backup.exists() or backup.stat().st_size == 0:
            raise RuntimeError("Backup SQLite não foi criado corretamente.")

        run_id = f"inflated-topics-{timestamp}-{uuid4().hex[:8]}"
        apply_plan(connection, plan, run_id)
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Falha na verificação de integridade após a transação.")

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"reclassify-inflated-topics-{timestamp}.json"
        report_path.write_text(
            json.dumps(report(plan, run_id, backup), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Aplicado. Backup: {backup}")
        print(f"Relatório: {report_path}")
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
