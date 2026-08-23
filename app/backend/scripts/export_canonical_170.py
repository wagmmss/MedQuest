import json

with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

all_modules_by_area = {}
for area_group in planner_data:
    area = area_group["area"]
    all_modules_by_area[area] = [m["theme"] for m in area_group.get("macroThemes", [])]

print("=== 170 CANONICAL MEDWAY MODULES ===")
for area, modules in all_modules_by_area.items():
    print(f"\n📌 {area} ({len(modules)} módulos):")
    for i, m in enumerate(modules):
        print(f"  [{i+1:02d}] {m}")

with open("canonical_modules_170.json", "w", encoding="utf-8") as f:
    json.dump(all_modules_by_area, f, ensure_ascii=False, indent=2)
