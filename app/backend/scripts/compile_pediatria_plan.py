import json

ped_modules = [
    {"name": "Desordens do Sistema Imune", "id": 68050, "theory_hours": 1.5, "foco_sp": True, "foco_rp": True},
    {"name": "Cardiopatias Congênitas", "id": 68040, "theory_hours": 1.6, "foco_sp": True, "foco_rp": False},
    {"name": "Arritmias, Síncope e PCR", "id": 68051, "theory_hours": 2.0, "foco_sp": True, "foco_rp": True},
    {"name": "Constipação Intestinal", "id": 68052, "theory_hours": 1.0, "foco_sp": False, "foco_rp": False},
    {"name": "Síndromes Diarreicas e Disabsortivas", "id": 68053, "theory_hours": 2.0, "foco_sp": True, "foco_rp": False},
    {"name": "Desordens Genéticas e Erros Inatos do Metabolismo", "id": 68038, "theory_hours": 1.5, "foco_sp": False, "foco_rp": False},
    {"name": "Infecção do Trato Urinário (ITU)", "id": 68046, "theory_hours": 1.2, "foco_sp": False, "foco_rp": False},
    {"name": "Doenças Exantemáticas", "id": 68048, "theory_hours": 1.54, "foco_sp": True, "foco_rp": True},
    {"name": "Imunizações", "id": 68044, "theory_hours": 2.5, "foco_sp": True, "foco_rp": True},
    {"name": "Parasitoses", "id": 68042, "theory_hours": 1.0, "foco_sp": False, "foco_rp": False},
    {"name": "Período Neonatal: Doenças Hematológicas", "id": 68035, "theory_hours": 1.29, "foco_sp": False, "foco_rp": True},
    {"name": "Período Neonatal: Doenças Infecciosas", "id": 68036, "theory_hours": 1.77, "foco_sp": True, "foco_rp": True},
    {"name": "Período Neonatal: Doenças do Metabolismo", "id": 68027, "theory_hours": 0.54, "foco_sp": False, "foco_rp": False},
    {"name": "Período Neonatal: Doenças Respiratórias", "id": 68026, "theory_hours": 0.88, "foco_sp": False, "foco_rp": False},
    {"name": "Período Neonatal: Doenças Neurológicas e Sensoriais", "id": 68045, "theory_hours": 1.29, "foco_sp": False, "foco_rp": False},
    {"name": "Sala de Parto", "id": 68039, "theory_hours": 2.26, "foco_sp": True, "foco_rp": True},
    {"name": "Alojamento Conjunto e Testes de Triagem Neonatal", "id": 68041, "theory_hours": 1.5, "foco_sp": True, "foco_rp": True},
    {"name": "Epilepsia e Síndromes Convulsivas", "id": 68049, "theory_hours": 1.5, "foco_sp": False, "foco_rp": False},
    {"name": "Distúrbios Carenciais", "id": 68054, "theory_hours": 1.5, "foco_sp": False, "foco_rp": False},
    {"name": "Nutrição na Pediatria", "id": 68047, "theory_hours": 1.5, "foco_sp": True, "foco_rp": True},
    {"name": "Nariz, Ouvido e Laringe", "id": 68030, "theory_hours": 1.5, "foco_sp": False, "foco_rp": True},
    {"name": "Distúrbios Obstrutivos", "id": 68028, "theory_hours": 2.5, "foco_sp": True, "foco_rp": True},
    {"name": "Segurança e Violência na Infância", "id": 68029, "theory_hours": 1.0, "foco_sp": False, "foco_rp": False},
    {"name": "Avaliação e Transtornos do Comportamento na Infância e Adolescência", "id": 68032, "theory_hours": 1.5, "foco_sp": True, "foco_rp": False},
    {"name": "Distúrbios Estaturais e Puberais", "id": 68033, "theory_hours": 1.5, "foco_sp": True, "foco_rp": False},
    {"name": "Crescimento e Desenvolvimento na Infância e Adolescência", "id": 68034, "theory_hours": 1.26, "foco_sp": True, "foco_rp": True},
    {"name": "Sepse, Choque Séptico e Outros tipos de Choque", "id": 68031, "theory_hours": 2.0, "foco_sp": False, "foco_rp": True},
    {"name": "Vasculites", "id": 82794, "theory_hours": 2.0, "foco_sp": True, "foco_rp": False}
]

for item in ped_modules:
    item["high_yield"] = item["foco_sp"] or item["foco_rp"]
    item["total_estimated_hours"] = round(item["theory_hours"] + 2.0, 2)

print(f"Compiled {len(ped_modules)} Pediatria modules:")
with open("pediatria_plan_compiled.json", "w", encoding="utf-8") as f:
    json.dump(ped_modules, f, ensure_ascii=False, indent=2)

for item in ped_modules:
    focos = []
    if item["foco_sp"]: focos.append("USP-SP")
    if item["foco_rp"]: focos.append("USP-RP")
    f_str = f"[{', '.join(focos)}]" if focos else ""
    print(f" - {item['name']}: {item['theory_hours']}h regular + 2h q = {item['total_estimated_hours']}h {f_str}")
