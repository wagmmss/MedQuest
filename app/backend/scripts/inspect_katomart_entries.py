import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

print(f"Total subtemas in katomart: {len(kat.get('subtemas', {}))}")
for k, v in list(kat.get("subtemas", {}).items())[:20]:
    print(f" - {k}: area={v.get('area')}, hours={v.get('regular_hours')}")
