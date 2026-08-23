import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

with open("preventiva_modules_raw.json", "r", encoding="utf-8") as f:
    modules = json.load(f)

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)
with open("pediatria_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_focos = {item["name"].lower(): item for item in sp if "Preventiva" in item.get("discipline_name", "") or "Social" in item.get("discipline_name", "")}
rp_focos = {item["name"].lower(): item for item in rp if "Preventiva" in item.get("discipline_name", "") or "Social" in item.get("discipline_name", "")}

# Exact Katomart durations mapping
kat_subs = kat.get("subtemas", {})

# Let's inspect Katomart entries for Preventiva
prev_plan = []
for m in modules:
    name = m["name"]
    mid = m["id"]
    
    # Check focus
    is_sp = name.lower() in sp_focos
    is_rp = name.lower() in rp_focos
    
    # Match katomart duration
    k_match = kat_subs.get(name)
    if not k_match:
        for k, v in kat_subs.items():
            if k.lower() == name.lower() or name.lower() in k.lower() or k.lower() in name.lower():
                k_match = v
                break
    
    dur = k_match.get("theory_hours", 1.5) if k_match else 1.5
    
    # Curated precise durations if needed:
    if "Bioética" in name: dur = 1.67
    elif "Análise Estatística" in name: dur = 2.0
    elif "Classificação" in name: dur = 1.6
    elif "Morbimortalidade" in name: dur = 1.5
    elif "demográficos" in name: dur = 1.5
    elif "Níveis de Prevenção" in name: dur = 1.9
    elif "Aspectos Históricos" in name: dur = 1.5
    elif "Evolução do SUS" in name: dur = 2.0
    elif "Atenção Primária" in name: dur = 2.23
    elif "Testes Diagnósticos" in name: dur = 2.0
    elif "Epidemias" in name: dur = 1.5
    elif "Notificação" in name: dur = 1.85
    elif "Trabalhador" in name: dur = 1.82

    prev_plan.append({
        "id": mid,
        "name": name,
        "foco_sp": is_sp,
        "foco_rp": is_rp,
        "high_yield": is_sp or is_rp,
        "theory_hours": round(dur, 2),
        "total_estimated_hours": round(dur + 2.0, 2)
    })

print(f"Compiled {len(prev_plan)} Preventiva modules:")
with open("preventiva_plan_compiled.json", "w", encoding="utf-8") as f:
    json.dump(prev_plan, f, ensure_ascii=False, indent=2)

for item in prev_plan:
    focos = []
    if item["foco_sp"]: focos.append("USP-SP")
    if item["foco_rp"]: focos.append("USP-RP")
    f_str = f"[{', '.join(focos)}]" if focos else ""
    print(f" - {item['name']}: {item['theory_hours']}h regular + 2h q = {item['total_estimated_hours']}h {f_str}")
