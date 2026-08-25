"""Auditoria não destrutiva da categorização de módulos."""

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
TAXONOMY_PATH = ROOT / "app" / "backend" / "data" / "taxonomy.json"
REPORT_PATH = ROOT / "docs" / "audits" / "module-categorization-audit-2026-08-25.md"

TOPIC_AREA = {
    "CM": "Clínica Médica", "CIR": "Cirurgia", "PED": "Pediatria",
    "GO": "Ginecologia e Obstetrícia", "GINECO": "Ginecologia e Obstetrícia",
    "OBST": "Ginecologia e Obstetrícia", "PREV": "Medicina Preventiva",
    "MPS": "Medicina Preventiva",
}


def main():
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    canonical = {(area["area"], theme["theme"]) for area in taxonomy for theme in area["macroThemes"]}
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    questions = db.execute("SELECT id, area, subtema, topic FROM questions ORDER BY id").fetchall()

    invalid = [q for q in questions if (q["area"], q["subtema"]) not in canonical]
    conflicts = []
    for question in questions:
        for tag in re.findall(r"\\(([^)]{2,10})\\)", question["topic"] or ""):
            expected_area = TOPIC_AREA.get(tag.strip().upper())
            if expected_area and expected_area != question["area"]:
                conflicts.append((question, tag.strip().upper(), expected_area))
                break

    area_counts = Counter(question["area"] for question in questions)
    lines = [
        "# Auditoria de categorização de módulos",
        "",
        "## Resultado estrutural",
        "",
        f"- Questões auditadas: **{len(questions)}**",
        f"- Pares área/subtema fora da taxonomia: **{len(invalid)}**",
        f"- Módulos canônicos com questões: **{len(set((q['area'], q['subtema']) for q in questions))}**",
        "",
        "## Distribuição por área",
        "",
    ]
    lines += [f"- {area}: {count}" for area, count in sorted(area_counts.items())]
    lines += [
        "",
        "## Alertas de revisão",
        "",
        "A marca entre parênteses no tema de origem (por exemplo, `CM`, `PED` e `CIR`) "
        "indica uma área diferente da categoria atual. Estes casos exigem revisão clínica; "
        "o relatório não altera o banco.",
        "",
        f"Total de alertas: **{len(conflicts)}**.",
        "",
        "| ID | Área atual | Módulo atual | Tema de origem | Área indicada |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for question, _tag, expected_area in conflicts:
        topic = (question["topic"] or "").replace("|", "\\|")
        lines.append(f"| {question['id']} | {question['area']} | {question['subtema']} | {topic} | {expected_area} |")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Auditadas: {len(questions)} | inválidas: {len(invalid)} | alertas: {len(conflicts)}")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
