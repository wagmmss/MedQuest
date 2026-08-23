import json

# Load 45 themes from clinica_extracted_themes.json
with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    t45 = json.load(f)

# Load existing taxonomy.json
with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

# Load katomart
with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

# Find clinica in taxonomy
cli_area = None
for a in tax:
    if "Clínica" in a.get("area", "") or "nica" in a.get("area", ""):
        cli_area = a
        break

# Build details map from existing macro themes if available
details_map = {}
if cli_area:
    for m in cli_area.get("macroThemes", []):
        details_map[m["theme"]] = m.get("details", [m["theme"]])

# Consolidate the 45 themes into canonical Medway macroThemes
new_cli_macro = []
seen = set()

# Load SP and RP focos for Clínica Médica
with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)
with open("pediatria_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_focos = {item["name"].lower() for item in sp if "Clínica" in item.get("discipline_name", "") or "nica" in item.get("discipline_name", "")}
rp_focos = {item["name"].lower() for item in rp if "Clínica" in item.get("discipline_name", "") or "nica" in item.get("discipline_name", "")}

for name, v in t45.items():
    theme_name = name
    if "Distúrbios da Hemostasia, Desordens Trombóticas" in name:
        theme_name = "Distúrbios da Hemostasia, Desordens Trombóticas e Transfusão de Hemocomponentes"
        
    if theme_name in seen:
        continue
    seen.add(theme_name)
    
    is_high_yield = theme_name.lower() in sp_focos or theme_name.lower() in rp_focos
    details = details_map.get(theme_name, [theme_name])
    
    new_cli_macro.append({
        "theme": theme_name,
        "highYield": is_high_yield,
        "dbSubtemas": [theme_name],
        "details": details
    })

if cli_area:
    cli_area["macroThemes"] = new_cli_macro

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print(f"Updated Clínica Médica to {len(new_cli_macro)} canonical themes in taxonomy.json!")
