import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

# Keep only the 5 clean canonical areas
canonical_map = {}
for a in tax:
    name = a.get("area", "")
    if "Cirurgia" in name:
        canonical_map["Cirurgia"] = a.get("macroThemes", [])
    elif "nica" in name:
        canonical_map["Clínica Médica"] = a.get("macroThemes", [])
    elif "Ginecologia" in name:
        canonical_map["Ginecologia e Obstetrícia"] = a.get("macroThemes", [])
    elif "Pediatria" in name:
        canonical_map["Pediatria"] = a.get("macroThemes", [])
    elif "Preventiva" in name and len(a.get("macroThemes", [])) > 5:
        canonical_map["Preventiva"] = a.get("macroThemes", [])

clean_tax = [
    {"area": "Cirurgia", "macroThemes": canonical_map["Cirurgia"]},
    {"area": "Clínica Médica", "macroThemes": canonical_map["Clínica Médica"]},
    {"area": "Ginecologia e Obstetrícia", "macroThemes": canonical_map["Ginecologia e Obstetrícia"]},
    {"area": "Pediatria", "macroThemes": canonical_map["Pediatria"]},
    {"area": "Preventiva", "macroThemes": canonical_map["Preventiva"]}
]

print(f"Clean taxonomy with 5 areas:")
total_modules = 0
for a in clean_tax:
    count = len(a["macroThemes"])
    total_modules += count
    print(f" - {a['area']}: {count} modules")
print(f"Total modules across all 5 areas: {total_modules}")

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(clean_tax, f, ensure_ascii=False, indent=2)

print("Saved clean 5-area taxonomy.json!")
