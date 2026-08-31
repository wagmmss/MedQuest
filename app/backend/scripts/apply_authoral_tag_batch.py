#!/usr/bin/env python3
"""Aplica um micro-lote editorial de recategorização baseado na tag de origem.

O arquivo de lote declara a categoria atual esperada e o destino canônico. A
execução interrompe a transação se qualquer questão tiver sido alterada desde a
revisão, preservando a rastreabilidade e a reversibilidade por lote.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", type=Path, help="JSON do lote editorial")
    parser.add_argument("--db", type=Path, default=BACKEND / "medquest.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    batch = load_json(args.batch)
    items = batch["items"]
    taxonomy = load_json(BACKEND / "data" / "canonical_taxonomy.json")
    subtema_map = load_json(BACKEND / "data" / "subtema_map.json")

    for item in items:
        target = item["target"]
        if target["area"] not in taxonomy or target["subtema"] not in taxonomy[target["area"]]:
            raise SystemExit(f"Destino não canônico: {target}")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    preview = []
    for item in items:
        row = conn.execute("SELECT id, topic, area, subtema FROM questions WHERE id = ?", (item["question_id"],)).fetchone()
        if row is None:
            raise SystemExit(f"Questão inexistente: {item['question_id']}")
        expected = item["expected"]
        if row["topic"] != item["source_tag"] or (row["area"], row["subtema"]) != (expected["area"], expected["subtema"]):
            raise SystemExit(f"Questão {item['question_id']} não confere com a revisão do lote")
        preview.append({"question_id": row["id"], "source_tag": row["topic"], "before": expected, "after": item["target"]})

    if not args.apply:
        print(json.dumps({"batch_id": batch["batch_id"], "mode": "dry_run", "items": preview}, ensure_ascii=False, indent=2))
        conn.close()
        return 0

    backup_dir = ROOT / "backups"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"medquest_{stamp}_pre-{batch['batch_id']}.db"
    destination = sqlite3.connect(backup)
    try:
        conn.backup(destination)
    finally:
        destination.close()

    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute("BEGIN IMMEDIATE")
        for item in items:
            expected, target = item["expected"], item["target"]
            changed = conn.execute(
                """UPDATE questions SET area = ?, subtema = ?, subtema_id = ?
                   WHERE id = ? AND topic = ? AND area = ? AND subtema = ?""",
                (target["area"], target["subtema"], subtema_map.get(target["subtema"]), item["question_id"],
                 item["source_tag"], expected["area"], expected["subtema"]),
            ).rowcount
            if changed != 1:
                raise RuntimeError(f"Falha de concorrência na questão {item['question_id']}")
            conn.execute(
                """INSERT INTO reclassification_audit
                   (question_id, old_area, old_subtema, new_area, new_subtema, confidence, rationale, model_used, applied, classified_at)
                   VALUES (?, ?, ?, ?, ?, 1.0, ?, ?, 1, ?)""",
                (item["question_id"], expected["area"], expected["subtema"], target["area"], target["subtema"],
                 f"{batch['batch_id']}; tag de origem: {item['source_tag']}; {item['rationale']}",
                 "authoral_source_tag_editorial", now),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    receipt = {"batch_id": batch["batch_id"], "applied": len(items), "backup": str(backup), "items": preview}
    receipt_path = args.batch.with_name(f"{batch['batch_id']}-applied-{stamp}.json")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
