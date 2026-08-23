import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

with open("go_plan_compiled.json", "r", encoding="utf-8") as f:
    go_plan = json.load(f)

for item in go_plan:
    name = item["name"]
    hours = item["theory_hours"]
    kat["subtemas"][name] = {
        "theory_hours": hours,
        "module": name,
        "match_confidence": 1.0
    }

with open("app/backend/scripts/katomartCourseDurations.json", "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=2)

print("Updated katomartCourseDurations.json with 37 GO modules!")
