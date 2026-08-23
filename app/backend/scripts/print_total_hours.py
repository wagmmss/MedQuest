import json

with open("app/backend/scripts/plannerData.json", "r", encoding="utf-8") as f:
    planner_data = json.load(f)

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

kat_subs = kat.get("subtemas", {})

results = []
grand_theory = 0.0
grand_practice = 0.0
grand_modules = 0

for area_group in planner_data:
    area = area_group.get("area", "")
    macros = area_group.get("macroThemes", [])
    
    area_theory = 0.0
    area_practice = 0.0
    
    for m in macros:
        theme = m.get("theme", "")
        db_subs = m.get("dbSubtemas", [theme])
        
        # Calculate theory hours for this macro theme
        theme_h = 0.0
        for s in db_subs:
            k = kat_subs.get(s, {})
            theme_h += k.get("theory_hours", 1.5)
            
        area_theory += theme_h
        area_practice += 2.0
        
    grand_theory += area_theory
    grand_practice += area_practice
    grand_modules += len(macros)
    
    results.append({
        "area": area,
        "modules": len(macros),
        "theory_hours": round(area_theory, 1),
        "practice_hours": round(area_practice, 1),
        "total_hours": round(area_theory + area_practice, 1)
    })

print("="*60)
print("RELATÓRIO DE TEMPO DE AULA E ESTUDO NAS 5 GRANDES ÁREAS")
print("="*60)
for r in results:
    print(f"Área: {r['area']}")
    print(f"  • Módulos: {r['modules']}")
    print(f"  • Horas de Aulas Teóricas: {r['theory_hours']}h")
    print(f"  • Horas de Questões (2h/tema): {r['practice_hours']}h")
    print(f"  • Carga Total de Estudo: {r['total_hours']}h")
    print("-" * 60)

print(f"TOTAL GERAL ({len(results)} Áreas):")
print(f"  • Total de Módulos: {grand_modules}")
print(f"  • Total de Vídeo/Aulas Teóricas: {grand_theory:.1f} horas ({grand_theory/24:.1f} dias de vídeo)")
print(f"  • Total de Treino Prático de Questões: {grand_practice:.1f} horas")
print(f"  • Carga Horária Completa do Curso: {grand_theory + grand_practice:.1f} horas")
print("="*60)
