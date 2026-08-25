"""Reordena e consolida seções do Template Ouro sem modificar seu conteúdo."""

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
ORDER = ["Gabarito", "Pulo do Gato", "Raciocínio Clínico", "Por que a Letra", "Análise dos Distratores"]
PATTERN = re.compile(
    r"(?mi)^\s*\*\*(Gabarito|Pulo do Gato|Raciocínio Clínico[^*]*|Por que a Letra[^*]*|Análise dos Distratores)\*\*:?"
)


def key(raw):
    lowered = raw.casefold()
    return next(item for item in ORDER if lowered.startswith(item.casefold()))


def needs_normalization(text):
    found = [(match.start(), key(match.group(1))) for match in PATTERN.finditer(text or "")]
    section_names = [name for _, name in found]
    return len(section_names) != len(set(section_names)) or [name for _, name in found] != sorted(section_names, key=ORDER.index)


def normalize(text):
    matches = list(PATTERN.finditer(text))
    if not matches:
        return text
    grouped = {name: [] for name in ORDER}
    original_headers = {}
    prefix = text[:matches[0].start()].strip()
    for index, match in enumerate(matches):
        section = key(match.group(1))
        original_headers.setdefault(section, match.group(1).strip())
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        if body:
            grouped[section].append(body)
    if prefix:
        grouped[key(match.group(1))].insert(0, prefix)
    output = []
    for section in ORDER:
        if grouped[section]:
            # Preserva o título de origem (inclusive a letra do gabarito).
            output.append(f"**{original_headers.get(section, section)}**:\n" + "\n\n".join(grouped[section]))
    return "\n\n".join(output).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT question_id, explanation_text FROM explanations").fetchall()
    changes = [(normalize(row["explanation_text"] or ""), row["question_id"]) for row in rows if needs_normalization(row["explanation_text"] or "")]
    print(f"Comentários com ordem/cabeçalhos a normalizar: {len(changes)}")
    if not args.apply:
        return
    backup = DB_PATH.with_name(f"{DB_PATH.name}.before-template-section-normalization-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(DB_PATH, backup)
    with conn:
        conn.executemany("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", changes)
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
