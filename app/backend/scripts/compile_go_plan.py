import json

# 1. Load Medway modules
with open("go_modules_raw.json", "r", encoding="utf-8") as f:
    medway_mods = json.load(f)

# 2. Load Katomart
with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

# 3. Load focos
with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)
with open("go_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_focos = {item["name"]: item for item in sp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")}
rp_focos = {item["name"]: item for item in rp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")}

# Exact / best curated mapping of Katomart theory hours to 37 Medway Modules
# Based on Medway course structure and katomart durations:
kat_subtemas = kat.get("subtemas", {})

# Let's define the curated mapping:
go_plan = []
for m in medway_mods:
    name = m["name"]
    mid = m["id"]
    
    # Match focus
    is_sp = name in sp_focos
    is_rp = name in rp_focos
    high_yield = is_sp or is_rp
    
    # Determine theory hours
    # We can match from katomart
    theory_hours = 1.0 # default baseline
    
    # Custom high-precision matching based on Medway catalog:
    if name == "Tumores do colo uterino":
        theory_hours = 1.78
    elif name == "Pré-Natal":
        theory_hours = 2.55
    elif name == "Rastreamento do Câncer de Colo Uterino":
        theory_hours = 1.78
    elif name == "Doenças do Corpo Uterino e Endométrio":
        theory_hours = 2.0
    elif name == "Diabetes mellitus na gravidez":
        theory_hours = 2.0
    elif name == "Outras doenças na gestação":
        theory_hours = 1.5
    elif name == "Síndromes Hipertensivas da Gestação":
        theory_hours = 1.31
    elif name == "Hepatites virais, HIV/AIDS e outras infecções na gestação":
        theory_hours = 2.0
    elif name == "Ciclo Menstrual":
        theory_hours = 1.24
    elif name == "Contracepção":
        theory_hours = 2.0
    elif name == "Climatério":
        theory_hours = 1.81
    elif name == "Amenorreias e Síndrome dos Ovários Policísticos":
        theory_hours = 2.37
    elif name == "Anatomia Pélvica":
        theory_hours = 1.0
    elif name == "Dor pélvica crônica":
        theory_hours = 1.83
    elif name == "Doença Inflamatória Pélvica e Violência Sexual":
        theory_hours = 1.69
    elif name == "Vulvovaginites":
        theory_hours = 0.93
    elif name == "Infertilidade conjugal":
        theory_hours = 1.41
    elif name == "Doenças Benignas da Mama":
        theory_hours = 1.5
    elif name == "Tumores Malignos da Mama":
        theory_hours = 2.0
    elif name == "Medicina Fetal":
        theory_hours = 1.5
    elif name == "Tumores dos Ovários":
        theory_hours = 1.5
    elif name == "Estática fetal, Pelve e Mecanismo de Parto":
        theory_hours = 1.8
    elif name == "Assistência ao Parto":
        theory_hours = 1.84
    elif name == "Rotura Prematura de Membranas Ovulares e Infecção Ovular":
        theory_hours = 1.0
    elif name == "Trabalho de parto prematuro":
        theory_hours = 1.04
    elif name == "Puerpério":
        theory_hours = 1.88
    elif name == "Sangramento da Primeira Metade da Gestação":
        theory_hours = 1.83
    elif name == "Sangramento da Segunda Metade da Gestação":
        theory_hours = 1.31
    elif name == "PALM-COEIN":
        theory_hours = 1.5
    elif name == "Sofrimento Fetal":
        theory_hours = 1.5
    elif name == "Úlceras genitais":
        theory_hours = 1.0
    elif name == "Incontinência Urinária e Prolapsos de Órgãos Pélvicos":
        theory_hours = 1.77
    elif name == "Patologias da Vulva e Vagina":
        theory_hours = 1.0
    elif name == "Conceitos em sexualidade":
        theory_hours = 0.5
    elif name == "Disfunções sexuais":
        theory_hours = 0.5
    elif name == "Fístulas":
        theory_hours = 0.5
    elif name == "Morte materna":
        theory_hours = 0.5

    go_plan.append({
        "id": mid,
        "name": name,
        "high_yield": high_yield,
        "foco_sp": is_sp,
        "foco_rp": is_rp,
        "theory_hours": round(theory_hours, 2),
        "total_estimated_hours": round(theory_hours + 2.0, 2)
    })

print(f"Generated plan for {len(go_plan)} Ginecologia e Obstetrícia modules:")
with open("go_plan_compiled.json", "w", encoding="utf-8") as f:
    json.dump(go_plan, f, ensure_ascii=False, indent=2)

for item in go_plan:
    focos = []
    if item["foco_sp"]: focos.append("USP-SP")
    if item["foco_rp"]: focos.append("USP-RP")
    f_str = f"[{', '.join(focos)}]" if focos else ""
    print(f" - {item['name']}: {item['theory_hours']}h regular + 2h q = {item['total_estimated_hours']}h {f_str}")
