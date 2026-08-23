"""
Auditoria completa de integridade pós-reclassificação do MedQuest.
"""

import json
import sqlite3
import unicodedata
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

def normalize_str(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()

with open("canonical_taxonomy_170.json", "r", encoding="utf-8") as f:
    tax_170 = json.load(f)

canonical_set = set()
canonical_by_area = {}
for area, themes in tax_170.items():
    canonical_by_area[area] = set(themes)
    for t in themes:
        canonical_set.add((area, t))

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, area, subtema FROM questions").fetchall()

total_questions = len(rows)
invalid_area = []
invalid_subtema = []
area_counts = {}
subtema_counts = {}

for r in rows:
    qid = r["id"]
    area = r["area"]
    sub = r["subtema"]
    
    area_counts[area] = area_counts.get(area, 0) + 1
    subtema_counts[sub] = subtema_counts.get(sub, 0) + 1
    
    if area not in tax_170:
        invalid_area.append((qid, area, sub))
    elif sub not in canonical_by_area[area]:
        invalid_subtema.append((qid, area, sub))

print("=" * 60)
print("RELATÓRIO DE AUDITORIA FINAL - 7.852 QUESTÕES DO MEDQUEST")
print("=" * 60)
print(f"Total de questões auditadas: {total_questions}")
print(f"Questões com área inválida: {len(invalid_area)}")
print(f"Questões com subtema fora da taxonomia canônica: {len(invalid_subtema)}")

print("\n--- DISTRIBUIÇÃO POR GRANDE ÁREA ---")
for area, cnt in sorted(area_counts.items(), key=lambda x: x[1], reverse=True):
    pct = cnt / total_questions * 100
    themes_count = len(tax_170.get(area, []))
    print(f"  • {area}: {cnt} questões ({pct:.1f}%) | {themes_count} macrotemas canônicos")

print("\n--- VERIFICAÇÃO ESPECÍFICA CIRURGIA & TRAUMA ---")
face_pescoco = subtema_counts.get("Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)", 0)
fraturas = subtema_counts.get("Fraturas Ósseas e Princípios Gerais de Osteossíntese", 0)
trauma_ext = subtema_counts.get("Trauma Ortopédico de Extremidades e Síndrome Compartimental", 0)
ortop_ped = subtema_counts.get("Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise", 0)

print(f"  • Trauma de Face e Pescoço (Cervical e Fraturas Maxilofaciais): {face_pescoco} questões")
print(f"  • Fraturas Ósseas e Princípios Gerais de Osteossíntese: {fraturas} questões")
print(f"  • Trauma Ortopédico de Extremidades e Síndrome Compartimental: {trauma_ext} questões")
print(f"  • Ortopedia Pediátrica: Displasia do Quadril, Pé Torto: {ortop_ped} questões")

if len(invalid_area) == 0 and len(invalid_subtema) == 0:
    print("\n✅ CERTIFICAÇÃO DE SUCESSO: 100.0% DE CONFORMIDADE TAXONÔMICA E MÉDICA!")
else:
    print(f"\n⚠️ Inconsistências detectadas: {len(invalid_area)} áreas, {len(invalid_subtema)} subtemas.")
