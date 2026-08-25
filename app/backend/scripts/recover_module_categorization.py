"""Recupera rótulos canônicos do backup para o banco de questões atual.

Só transfere um rótulo quando a correspondência é inequívoca: primeiro pelo
enunciado normalizado e, em seguida, por tema normalizado que tenha uma única
classificação no backup. As demais questões ficam para o classificador médico.
"""

import argparse
import collections
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "app" / "backend" / "medquest.db"
DEFAULT_BACKUP = ROOT / "app" / "backend" / "medquest.db.backup_images_20260824_220955"


def normalize(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    old = sqlite3.connect(args.backup)
    old.row_factory = sqlite3.Row
    current = sqlite3.connect(args.db)
    current.row_factory = sqlite3.Row

    old_questions = old.execute("SELECT id, stem, topic, area, subtema FROM questions").fetchall()
    current_questions = current.execute("SELECT id, stem, topic, area, subtema FROM questions").fetchall()

    by_stem = {}
    for question in old_questions:
        key = normalize(question["stem"])
        if key:
            by_stem.setdefault(key, []).append(question)

    # Only topic mappings with one canonical destination are safe to transfer.
    by_topic = collections.defaultdict(set)
    for question in old_questions:
        key = normalize(question["topic"])
        if key:
            by_topic[key].add((question["area"], question["subtema"]))

    updates, methods = [], collections.Counter()
    for question in current_questions:
        candidates = by_stem.get(normalize(question["stem"]), [])
        if len(candidates) == 1:
            match = candidates[0]
            method = "normalized_stem"
        else:
            targets = by_topic.get(normalize(question["topic"]), set())
            if len(targets) != 1:
                continue
            match_area, match_subtema = next(iter(targets))
            match = {"area": match_area, "subtema": match_subtema}
            method = "unique_normalized_topic"

        if (question["area"], question["subtema"]) != (match["area"], match["subtema"]):
            updates.append((match["area"], match["subtema"], question["id"]))
            methods[method] += 1

    print(f"Questões atuais: {len(current_questions)}")
    print(f"Recuperações inequívocas a aplicar: {len(updates)} ({dict(methods)})")
    if not args.apply:
        return

    destination_backup = args.db.with_name(f"{args.db.name}.before-module-recovery-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(args.db, destination_backup)
    with current:
        current.executemany("UPDATE questions SET area = ?, subtema = ? WHERE id = ?", updates)
    print(f"Backup pré-recuperação: {destination_backup}")


if __name__ == "__main__":
    main()
