import sqlite3
import json
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

# Load plannerData.json
with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

# Extract all canonical themes by area
canonical_by_area = {}
all_canonical_themes = set()
for area_group in planner_data:
    area = area_group["area"]
    canonical_by_area[area] = set()
    for m in area_group.get("macroThemes", []):
        theme = m["theme"]
        canonical_by_area[area].add(theme)
        all_canonical_themes.add(theme)
        for s in m.get("dbSubtemas", []):
            canonical_by_area[area].add(s)
            all_canonical_themes.add(s)

print(f"Total canonical themes in taxonomy: {len(all_canonical_themes)}")

# 1. Check all questions
total_q = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
missing_area = conn.execute("SELECT COUNT(*) FROM questions WHERE area IS NULL OR area = ''").fetchone()[0]
missing_sub = conn.execute("SELECT COUNT(*) FROM questions WHERE subtema IS NULL OR subtema = ''").fetchone()[0]

print(f"\n1. AUDIT DE NULIDADE:")
print(f" - Total de questões no banco: {total_q}")
print(f" - Questões sem área: {missing_area}")
print(f" - Questões sem subtema: {missing_sub}")

# 2. Check taxonomy alignment
subtema_counts = conn.execute("""
    SELECT area, subtema, COUNT(*) as count 
    FROM questions 
    GROUP BY area, subtema 
    ORDER BY count DESC
""").fetchall()

unmapped_subtemas = []
mapped_count = 0
unmapped_count = 0

for r in subtema_counts:
    area = r["area"]
    sub = r["subtema"]
    cnt = r["count"]
    if sub in all_canonical_themes:
        mapped_count += cnt
    else:
        unmapped_count += cnt
        unmapped_subtemas.append((area, sub, cnt))

print(f"\n2. AUDIT DE TAXONOMIA:")
print(f" - Questões com subtema 100% canônico: {mapped_count} ({mapped_count/total_q*100:.1f}%)")
print(f" - Questões com subtema NÃO canônico / legado: {unmapped_count} ({unmapped_count/total_q*100:.1f}%)")

if unmapped_subtemas:
    print(f"\nSubtemas não canônicos encontrados ({len(unmapped_subtemas)} tipos):")
    for a, s, c in unmapped_subtemas[:15]:
        print(f"   • [{a}] '{s}': {c} questões")

# 3. Check disproportionate clusters (e.g. > 200 questions in 1 subtema)
print(f"\n3. SUBTEMAS COM CONCENTRAÇÃO MUITO ALTA (> 100 questões):")
for r in subtema_counts:
    if r["count"] >= 100:
        print(f"   • [{r['area']}] {r['subtema']}: {r['count']} questões")

# 4. Check subtemas with ZERO questions
print(f"\n4. SUBTEMAS CANÔNICOS COM 0 QUESTÕES NO BANCO:")
subtemas_in_db = {r["subtema"] for r in subtema_counts if r["subtema"]}
zero_q_themes = []
for area_name, themes in canonical_by_area.items():
    for t in sorted(themes):
        if t not in subtemas_in_db:
            zero_q_themes.append((area_name, t))

print(f"Total de temas com 0 questões: {len(zero_q_themes)}")
for a, t in zero_q_themes:
    print(f"   • [{a}] {t}")
