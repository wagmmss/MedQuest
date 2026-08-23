import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

print("Katomart Ginecologia e Obstetrícia keys:")
go_keys = {}
for k, v in kat.get("subtemas", {}).items():
    if v.get("area") in ["Ginecologia e Obstetrícia", "Ginecologia", "Obstetrícia", "GO"]:
        go_keys[k] = v

print(f"Total GO entries in katomart: {len(go_keys)}")
for k, v in go_keys.items():
    print(f" - {k}: {v.get('regular_hours', 0)}h (Module: {v.get('course_module')})")
