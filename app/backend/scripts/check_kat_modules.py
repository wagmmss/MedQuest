import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

modules = kat.get("modules", {})
print(f"Total modules in katomart: {len(modules)}")
for k, v in sorted(modules.items()):
    print(f" - {k}: {v.get('regular_hours', 0)}h (Lessons: {len(v.get('lessons', []))})")
