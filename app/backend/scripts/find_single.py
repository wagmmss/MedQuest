import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for a in tax:
    for m in a.get("macroThemes", []):
        if len(m.get("details", [])) <= 1:
            print("Single item theme:", repr(m["theme"]), "in Area:", a["area"])
