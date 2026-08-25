"""Remove duplicatas por enunciado normalizado, preservando dados vinculados."""

import argparse
import collections
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
REPORT_PATH = ROOT / "docs" / "audits" / "deduplicate-exact-questions-2026-08-25.md"


def normalize(value):
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def score(conn, question):
    qid = question["id"]
    alt_count, valid_correct = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(is_correct), 0) FROM alternatives WHERE question_id = ?", (qid,)
    ).fetchone()
    explanation = conn.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)).fetchone()
    text = explanation[0] if explanation else ""
    image_count = conn.execute("SELECT COUNT(*) FROM question_images WHERE question_id = ?", (qid,)).fetchone()[0]
    value = min(alt_count, 5) * 20 + int(valid_correct == 1) * 40 + min(len(text or ""), 5000) / 100 + image_count
    if question["editorial_status"] != "autoral":
        value += 10
    if "anulada" in normalize(text):
        value -= 30
    # Em empate, mantém o menor ID: é a primeira ocorrência importada.
    return value


def migrate_references(conn, source_id, keeper_id):
    conn.execute("UPDATE attempts SET question_id = ? WHERE question_id = ?", (keeper_id, source_id))
    for table in ("favorites", "spaced_repetition"):
        rows = conn.execute(f"SELECT * FROM {table} WHERE question_id = ?", (source_id,)).fetchall()
        for row in rows:
            values = dict(row)
            values["question_id"] = keeper_id
            columns = list(values)
            conn.execute(f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", [values[col] for col in columns])
        conn.execute(f"DELETE FROM {table} WHERE question_id = ?", (source_id,))
    conn.execute("UPDATE flashcards SET question_id = ? WHERE question_id = ?", (keeper_id, source_id))
    conn.execute("UPDATE reclassification_audit SET question_id = ? WHERE question_id = ?", (keeper_id, source_id))

    known_image_paths = {row[0] for row in conn.execute("SELECT file_path FROM question_images WHERE question_id = ?", (keeper_id,))}
    for image in conn.execute("SELECT id, file_path FROM question_images WHERE question_id = ?", (source_id,)).fetchall():
        if image["file_path"] in known_image_paths:
            conn.execute("DELETE FROM question_images WHERE id = ?", (image["id"],))
        else:
            conn.execute("UPDATE question_images SET question_id = ? WHERE id = ?", (keeper_id, image["id"]))
            known_image_paths.add(image["file_path"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    questions = conn.execute("SELECT id, source_file, source_number, editorial_status, stem FROM questions ORDER BY id").fetchall()
    by_stem = collections.defaultdict(list)
    for question in questions:
        key = normalize(question["stem"])
        if key:
            by_stem[key].append(question)
    groups = [group for group in by_stem.values() if len(group) > 1]
    plan = []
    for group in groups:
        keeper = max(group, key=lambda question: (score(conn, question), -question["id"]))
        for duplicate in group:
            if duplicate["id"] != keeper["id"]:
                plan.append((keeper, duplicate))
    print(f"Grupos exatos: {len(groups)} | questões a remover: {len(plan)}")
    if not args.apply:
        return

    backup = DB_PATH.with_name(f"{DB_PATH.name}.before-deduplicate-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(DB_PATH, backup)
    with conn:
        for keeper, duplicate in plan:
            migrate_references(conn, duplicate["id"], keeper["id"])
            conn.execute("DELETE FROM alternatives WHERE question_id = ?", (duplicate["id"],))
            conn.execute("DELETE FROM explanations WHERE question_id = ?", (duplicate["id"],))
            conn.execute("DELETE FROM questions WHERE id = ?", (duplicate["id"],))

    REPORT_PATH.write_text(
        "# Deduplicação de questões\n\n"
        f"- Grupos de enunciado idêntico: **{len(groups)}**\n"
        f"- Questões removidas: **{len(plan)}**\n"
        f"- Backup: `{backup.name}`\n\n"
        "A versão preservada em cada grupo foi escolhida por completude de alternativas, gabarito, explicação, imagens e status editorial. "
        "Vínculos de estudo, auditoria e imagens foram migrados antes da remoção.\n",
        encoding="utf-8",
    )
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
