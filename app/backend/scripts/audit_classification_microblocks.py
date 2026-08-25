"""Independent, read-only integrity audit for the question taxonomy.

It divides the corpus into small, reproducible review blocks and checks three
failure modes that a rule-based reclassifier can miss: invalid taxonomy values,
one source topic assigned to different canonical themes, and identical stems
assigned differently.  The output is a JSON report; it never updates the DB.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
DATABASE = BACKEND / "medquest.db"
TAXONOMY = BACKEND / "data" / "taxonomy.json"
REPORT = BACKEND / "data" / "classification_microblock_audit.json"
BLOCK_SIZE = 20


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def load_allowed_pairs() -> set[tuple[str, str]]:
    catalog = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    pairs: set[tuple[str, str]] = set()
    for area in catalog:
        for macro in area.get("macroThemes", []):
            for subtema in macro.get("dbSubtemas", []):
                pairs.add((area["area"], subtema))
    return pairs


def compact_question(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "topic": row["topic"] or "",
        "subtema": row["subtema"] or "",
        "stem_preview": re.sub(r"\s+", " ", row["stem"] or "")[:280],
    }


def main() -> None:
    allowed_pairs = load_allowed_pairs()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, area, topic, subtema, stem FROM questions ORDER BY area, subtema, topic, id"
    ).fetchall()

    invalid = [compact_question(row) | {"area": row["area"] or ""} for row in rows
               if (row["area"], row["subtema"]) not in allowed_pairs]

    by_source_topic: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
    by_stem: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        by_source_topic[(row["area"] or "", normalize(row["topic"]))].append(row)
        normalized_stem = normalize(row["stem"])
        if normalized_stem:
            by_stem[normalized_stem].append(row)

    topic_conflicts = []
    for (area, source_topic), group in sorted(by_source_topic.items()):
        assigned = sorted({row["subtema"] or "" for row in group})
        if len(assigned) > 1:
            topic_conflicts.append({
                "area": area,
                "source_topic": source_topic,
                "canonical_subtemas": assigned,
                "question_ids": [row["id"] for row in group],
            })

    stem_conflicts = []
    for group in by_stem.values():
        assigned = sorted({(row["area"] or "", row["subtema"] or "") for row in group})
        if len(group) > 1 and len(assigned) > 1:
            stem_conflicts.append({
                "canonical_assignments": [{"area": area, "subtema": subtema} for area, subtema in assigned],
                "questions": [compact_question(row) | {"area": row["area"] or ""} for row in group],
            })

    # These blocks make a manual semantic audit restartable without reshuffling.
    blocks = []
    for index in range(0, len(rows), BLOCK_SIZE):
        group = rows[index:index + BLOCK_SIZE]
        digest = hashlib.sha256(
            ";".join(f"{row['id']}|{row['area']}|{row['subtema']}" for row in group).encode()
        ).hexdigest()[:12]
        blocks.append({
            "number": index // BLOCK_SIZE + 1,
            "size": len(group),
            "signature": digest,
            "questions": [compact_question(row) | {"area": row["area"] or ""} for row in group],
        })

    payload = {
        "database": str(DATABASE),
        "block_size": BLOCK_SIZE,
        "questions_audited": len(rows),
        "microblocks": len(blocks),
        "invalid_taxonomy_assignments": invalid,
        "source_topic_conflicts": topic_conflicts,
        "duplicate_stem_conflicts": stem_conflicts,
        "blocks": blocks,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Questions audited: {len(rows)}")
    print(f"Microblocks: {len(blocks)} (max {BLOCK_SIZE} questions each)")
    print(f"Invalid taxonomy assignments: {len(invalid)}")
    print(f"Source-topic conflicts: {len(topic_conflicts)}")
    print(f"Duplicate-stem conflicts: {len(stem_conflicts)}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
