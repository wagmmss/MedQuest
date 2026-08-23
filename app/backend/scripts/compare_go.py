import json
import sqlite3

with open('medway_modules.json', 'r', encoding='utf-8') as f:
    mods = json.load(f)

db = sqlite3.connect('app/backend/medquest.db')
cursor = db.cursor()

# Get all subtemas in GO
go_subtemas = cursor.execute("SELECT DISTINCT subtema, COUNT(*) FROM questions WHERE area = 'Ginecologia e Obstetrícia' GROUP BY subtema").fetchall()

print(f"Total Medway GO modules: {len(mods)}")
print(f"Total DB GO subtemas: {len(go_subtemas)}")

medway_names = [m['name'] for m in mods]
print("\nMedway Modules:")
for i, name in enumerate(medway_names):
    print(f"  {i+1}. {name}")

print("\nDB Subtemas in GO (sample):")
for st, count in go_subtemas[:15]:
    print(f"  - {st} ({count} questões)")
