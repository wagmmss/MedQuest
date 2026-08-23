import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

for k in sorted(kat["subtemas"].keys()):
    v = kat["subtemas"][k]
    print(f"'{k}' -> {v.get('theory_hours')}h (module: {v.get('module')})")
