import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for a in tax:
    if a["area"] == "Preventiva":
        a["area"] = "Medicina Preventiva"

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print("Updated area name to Medicina Preventiva in taxonomy.json!")
