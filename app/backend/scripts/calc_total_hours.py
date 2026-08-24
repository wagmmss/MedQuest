import json

# Load plannerData.json
with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

# Load katomart durations
with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

kat_subs = kat.get("subtemas", {})

area_stats = {}

for area_group in planner_data:
    area_name = area_group.get("area", "")
    macros = area_group.get("macroThemes", [])
    
    total_theory = 0.0
    total_practice = 0.0
    module_count = len(macros)
    module_list = []
    
    for m in macros:
        theme = m.get("theme", "")
        db_subs = m.get("dbSubtemas", [theme])
        
        # Get theory hours
        theme_hours = 0.0
        for s in db_subs:
            k = kat_subs.get(s, {})
            h = k.get("theory_hours", 1.5)
            theme_hours += h
            
        theory_h = round(theme_hours, 2)
        practice_h = 2.0
        total_h = round(theory_h + practice_h, 2)
        
        total_theory += theory_h
        total_practice += practice_h
        module_list.append((theme, theory_h, total_h, m.get("highYield", False)))
        
    area_stats[area_name] = {
        "module_count": module_count,
        "total_theory_hours": round(total_theory, 2),
        "total_practice_hours": round(total_practice, 2),
        "total_study_hours": round(total_theory + total_practice, 2),
        "modules": module_list
    }

grand_theory = sum(s["total_theory_hours"] for s in area_stats.values())
grand_practice = sum(s["total_practice_hours"] for s in area_stats.values())
grand_total = sum(s["total_study_hours"] for s in area_stats.values())
grand_modules = sum(s["module_count"] for s in area_stats.values())

print(f"=== ESTATÍSTICAS GERAIS (5 GRANDES ÁREAS) ===")
print(f"Total de Módulos / Temas: {grand_modules}")
print(f"Total de Aulas Teóricas: {grand_theory:.1f} horas")
print(f"Total de Treino de Questões (2h/tema): {grand_practice:.1f} horas")
print(f"Total Geral de Estudos: {grand_total:.1f} horas ({grand_total/24:.1f} dias ininterruptos)")

print(f"\n=== DETALHAMENTO POR ÁREA ===")
for area, s in sorted(area_stats.items(), key=lambda x: x[1]["total_theory_hours"], reverse=True):
    print(f"\n[+] {area}:")
    print(f"   - Modulos: {s['module_count']}")
    print(f"   - Aulas Teoricas: {s['total_theory_hours']} horas ({s['total_theory_hours']/s['module_count']:.2f}h/modulo)")
    print(f"   - Treino de Questoes: {s['total_practice_hours']} horas")
    print(f"   - Carga Total: {s['total_study_hours']} horas")

with open("tempo_aulas_report.json", "w", encoding="utf-8") as f:
    json.dump({
        "grand_theory": grand_theory,
        "grand_practice": grand_practice,
        "grand_total": grand_total,
        "grand_modules": grand_modules,
        "areas": area_stats
    }, f, ensure_ascii=False, indent=2)
