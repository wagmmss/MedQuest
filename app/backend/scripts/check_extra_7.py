import json

with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    t45 = json.load(f)

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

tax_cli = []
for a in tax:
    if "Clínica" in a.get("area", "") or "nica" in a.get("area", ""):
        tax_cli = [m["theme"] for m in a.get("macroThemes", [])]

names_45 = list(t45.keys())

extra = [name for name in tax_cli if name not in names_45]
print("Extra 7 themes in taxonomy.json:")
for e in extra:
    print(f" - {e}")
