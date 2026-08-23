import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for area_data in tax:
    area = area_data["area"]
    single_count = 0
    multi_count = 0
    for macro in area_data.get("macroThemes", []):
        details = macro.get("details", [])
        if len(details) <= 1:
            single_count += 1
        else:
            multi_count += 1
    print(f"Area: {area} -> Single-item details: {single_count}, Multi-item details: {multi_count}")
