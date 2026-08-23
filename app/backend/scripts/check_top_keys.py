import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

print("Top keys:", list(kat.keys()))
