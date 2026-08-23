import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for a in tax:
    if a["area"] == "Cirurgia":
        for m in a["macroThemes"]:
            if "Fratura" in m["theme"] or "Cabe" in m["theme"]:
                print("Theme:", repr(m["theme"]), "dbSubtemas:", repr(m.get("dbSubtemas")))
