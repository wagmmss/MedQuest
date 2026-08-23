import json

with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

kat_subs = kat.get("subtemas", {})

print(f"Total area groups in plannerData: {len(planner_data)}")
for a in planner_data:
    area = a.get("area", "")
    macros = a.get("macroThemes", [])
    total_h = sum(kat_subs.get(m.get("theme"), {}).get("theory_hours", 1.5) for m in macros)
    print(f" - {area}: {len(macros)} modules | {total_h:.2f}h theory")
