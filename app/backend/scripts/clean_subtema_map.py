import json

# Load existing subtema map
with open("app/backend/data/subtema_map.json", "r", encoding="utf-8") as f:
    smap = json.load(f)

# Load catalog
with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

valid_subs = set()
for area in taxonomy:
    for macro in area.get("macroThemes", []):
        valid_subs.update(macro.get("dbSubtemas", []))

clean_map = {k: v for k, v in smap.items() if k in valid_subs}
print(f"Cleaned subtema map from {len(smap)} to {len(clean_map)} entries.")

with open("app/backend/data/subtema_map.json", "w", encoding="utf-8") as f:
    json.dump(clean_map, f, ensure_ascii=False, indent=2)

print("Saved clean subtema_map.json!")
