import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

for k, v in list(kat.get("subtemas", {}).items())[:10]:
    print(k, "->", v)
