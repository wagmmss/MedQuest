"""Safe first stage of the AI-assisted classification-review pipeline.

Creates a review run and exports only suspicious questions as packets. It never
updates the published area/subtema columns and makes no network/API calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_DB = BACKEND / "medquest.db"
TAXONOMY_PATH = BACKEND / "data" / "taxonomy.json"
MIGRATION_PATH = BACKEND / "migrations" / "006_classification_review.sql"
DEFAULT_OUTPUT = BACKEND / "data" / "classification_review_pilot.json"
PIPELINE_VERSION = "classification-review-pilot-v1"

TARGETS = (
    ("Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)",
     r"\baps\b|atencao primaria|atencao basica|estrategia saude da familia|\besf\b|medicina de familia|\bmfc\b|\bmccp\b|metodo clinico centrado|genograma|ecomapa|\bsoap\b|abordagem familiar|territoriali|adscric|longitudinalidade|coordenacao do cuidado|projeto terapeutico singular|clinica ampliada|\bnasf\b|visita domiciliar"),
    ("Ginecologia e Obstetrícia", "Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose",
     r"sangramento uterino|\bsua\b|palm.?coein|leiomioma|miomatose|fibromioma|adenomiose|sangramento anormal|sangramento menstrual|metrorragia|menorragia"),
    ("Clínica Médica", "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
     r"\bidos[oa]\b|geriatr|demenc|alzheimer|corpusculos de lewy|corpos de lewy|fragilidade|senescen|senilidad|avaliacao geriatrica|avaliacao global|escala geriatrica|\bqueda|\bquedas|polifarmacia|sarcopenia|imobilidade|delirium|cuidados paliativos|diretiva antecipada|capacidade funcional"),
)


def normalized(value: str | None) -> str:
    value = unicodedata.normalize("NFD", value or "")
    return "".join(char for char in value if unicodedata.category(char) != "Mn").lower()


def load_taxonomy() -> tuple[dict[str, list[str]], str]:
    raw = TAXONOMY_PATH.read_bytes()
    catalog = json.loads(raw)
    taxonomy = {
        area["area"]: [subtema for macro in area["macroThemes"] for subtema in macro["dbSubtemas"]]
        for area in catalog
    }
    return taxonomy, hashlib.sha256(raw).hexdigest()


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))


def alternatives_for(connection: sqlite3.Connection, question_id: int) -> list[dict[str, str]]:
    return [dict(row) for row in connection.execute(
        "SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (question_id,)
    )]


def packet(row: sqlite3.Row, taxonomy: dict[str, list[str]], reason: str) -> dict[str, object]:
    return {
        "question_id": row["id"],
        "current": {"area": row["area"], "subtema": row["subtema"]},
        "source_topic": row["topic"] or "",
        "stem": row["stem"] or "",
        "explanation": row["explanation_text"] or "",
        "allowed_taxonomy": taxonomy,
        "triage_reason": reason,
        "required_output": {
            "decision": "classify or abstain",
            "evidence": "short clinical evidence from the question",
            "alternatives": "up to three canonical candidates",
        },
    }


def create_pilot(connection: sqlite3.Connection, output: Path) -> tuple[str, int]:
    taxonomy, taxonomy_hash = load_taxonomy()
    connection.row_factory = sqlite3.Row
    selected: list[tuple[sqlite3.Row, str]] = []
    for area, subtema, pattern in TARGETS:
        rows = connection.execute(
            """SELECT q.id, q.area, q.subtema, q.topic, q.subtema_orig, q.stem, e.explanation_text
               FROM questions q LEFT JOIN explanations e ON e.question_id = q.id
               WHERE q.area = ? AND q.subtema = ? ORDER BY q.id""",
            (area, subtema),
        ).fetchall()
        for row in rows:
            # Explanations may mention differential diagnoses and must not remove
            # a question from the queue merely because of an incidental term.
            evidence_source = normalized(" ".join(str(row[key] or "") for key in ("topic", "subtema_orig", "stem")))
            if not re.search(pattern, evidence_source):
                selected.append((row, "No direct textual evidence supports the current fallback theme."))

    selected.sort(key=lambda item: item[0]["id"])
    input_hash = hashlib.sha256(
        "|".join(f"{row['id']}:{row['area']}:{row['subtema']}" for row, _ in selected).encode("utf-8")
    ).hexdigest()
    run_id = f"clr-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC).isoformat()
    with connection:
        connection.execute(
            "INSERT INTO classification_runs (id, taxonomy_version, pipeline_version, input_hash, status, created_at, notes) VALUES (?, ?, ?, ?, 'created', ?, ?)",
            (run_id, taxonomy_hash, PIPELINE_VERSION, input_hash, now, "Read-only pilot for suspected fallback assignments."),
        )
        for row, reason in selected:
            connection.execute(
                """INSERT INTO classification_proposals
                   (run_id, question_id, reviewer_role, decision, confidence, evidence, alternatives_json, status, created_at)
                   VALUES (?, ?, 'triage', 'abstain', NULL, ?, '[]', 'needs_human_review', ?)""",
                (run_id, row["id"], reason, now),
            )

    packets = []
    for row, reason in selected:
        value = packet(row, taxonomy, reason)
        value["alternatives"] = alternatives_for(connection, row["id"])
        packets.append(value)
    output.write_text(json.dumps({"run_id": run_id, "questions": packets}, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_id, len(packets)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--create-pilot", action="store_true", help="Create an audit run and review packets; never updates question classifications.")
    args = parser.parse_args()
    if not args.create_pilot:
        parser.error("Use --create-pilot. This tool intentionally has no direct-apply mode.")
    with sqlite3.connect(args.db) as connection:
        ensure_schema(connection)
        run_id, count = create_pilot(connection, args.output)
    print(f"Created review run: {run_id}")
    print(f"Questions queued: {count}")
    print(f"Review packet: {args.output}")


if __name__ == "__main__":
    main()
