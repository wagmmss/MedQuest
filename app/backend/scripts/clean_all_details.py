import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for a in tax:
    for m in a.get("macroThemes", []):
        m["details"] = []

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print("Cleaned details array in taxonomy.json for all themes!")
