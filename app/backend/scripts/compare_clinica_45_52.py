import json

with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    t45 = json.load(f)

print(f"--- 45 Themes in clinica_extracted_themes.json ---")
names_45 = []
for i, t in enumerate(t45):
    name = t.get("name") or t.get("title") or t.get("module")
    hours = t.get("lesson_hours") or t.get("theory_hours") or 0
    names_45.append(name)
    print(f"[{i+1:02d}] {name} ({hours}h)")

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

tax_cli = []
for a in tax:
    if "Clínica" in a.get("area", "") or "nica" in a.get("area", ""):
        tax_cli = [m["theme"] for m in a.get("macroThemes", [])]

print(f"\n--- 52 Themes in taxonomy.json for Clínica Médica ---")
for i, name in enumerate(tax_cli):
    in_45 = "✅ in 45" if name in names_45 else "❌ EXTRA"
    print(f"[{i+1:02d}] {name} | {in_45}")

extra = [name for name in tax_cli if name not in names_45]
missing = [name for name in names_45 if name not in tax_cli]
print(f"\nExtra in taxonomy ({len(extra)}): {extra}")
print(f"Missing from taxonomy ({len(missing)}): {missing}")
