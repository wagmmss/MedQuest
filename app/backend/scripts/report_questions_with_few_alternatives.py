"""Gera relatório das questões que não têm o conjunto objetivo completo."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
OUT = ROOT / "docs" / "audits" / "questions-with-few-alternatives-2026-08-25.md"

db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
rows = db.execute("""
    SELECT q.id, q.source_file, q.source_number, q.area, q.subtema, q.stem,
           COUNT(a.id) AS alternatives,
           SUM(CASE WHEN a.text LIKE 'Questão dissertativa%' THEN 1 ELSE 0 END) AS discursive
    FROM questions q LEFT JOIN alternatives a ON a.question_id = q.id
    GROUP BY q.id HAVING COUNT(a.id) < 4 ORDER BY q.source_file, q.source_number, q.id
""").fetchall()
discursive = [row for row in rows if row["discursive"]]
objective = [row for row in rows if not row["discursive"]]
lines = [
    "# Questões com menos de quatro alternativas",
    "",
    f"- Total: **{len(rows)}**",
    f"- Discursivas (formato esperado): **{len(discursive)}**",
    f"- Objetivas incompletas: **{len(objective)}**",
    "",
    "| ID | Origem | Nº | Alternativas | Área | Módulo | Enunciado |",
    "| ---: | --- | ---: | ---: | --- | --- | --- |",
]
for row in rows:
    stem = " ".join((row["stem"] or "").split()).replace("|", "\\|")
    kind = "discursiva" if row["discursive"] else str(row["alternatives"])
    lines.append(f"| {row['id']} | {row['source_file']} | {row['source_number'] or ''} | {kind} | {row['area']} | {row['subtema']} | {stem[:220]} |")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Total={len(rows)} discursivas={len(discursive)} objetivas_incompletas={len(objective)}")
print(OUT)
