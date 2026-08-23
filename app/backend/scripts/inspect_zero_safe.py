import sqlite3
import json

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

db_counts = {}
rows = conn.execute("SELECT area, subtema, COUNT(*) as count FROM questions GROUP BY area, subtema").fetchall()
for r in rows:
    db_counts[(r["area"], r["subtema"])] = r["count"]

zero_themes_by_area = {}
total_zeros = 0
total_themes = 0

for area_group in planner_data:
    area = area_group["area"]
    zero_themes_by_area[area] = []
    macros = area_group.get("macroThemes", [])
    total_themes += len(macros)
    
    for m in macros:
        theme = m["theme"]
        db_subs = m.get("dbSubtemas", [theme])
        
        q_count = sum(db_counts.get((area, s), 0) for s in db_subs)
        
        if q_count == 0:
            zero_themes_by_area[area].append((theme, m.get("highYield", False)))
            total_zeros += 1

print(f"Total Canonical Themes: {total_themes}")
print(f"Total Themes with 0 Questions: {total_zeros}")

for area, zeros in zero_themes_by_area.items():
    print(f"\nArea: {area} ({len(zeros)} temas com 0 questoes):")
    for name, hy in zeros:
        foco = "[Foco USP]" if hy else ""
        print(f" - {name} {foco}")
