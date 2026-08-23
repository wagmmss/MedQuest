import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

for a in tax:
    if a["area"] == "Cirurgia":
        for m in a.get("macroThemes", []):
            if "Queimaduras" in m["theme"] and "PED" in m["theme"]:
                m["theme"] = "Particularidades das Queimaduras na Faixa Etária Pediátrica"
                m["dbSubtemas"] = ["Particularidades das Queimaduras na Faixa Etária Pediátrica"]
                m["details"] = [
                    "Cálculo de área de superfície corporal queimada em crianças (Tabela de Lund-Browder)",
                    "Reposição volêmica na criança com fórmula de Parkland associada a soro de manutenção",
                    "Prevenção de hipotermia, analgesia e complicações metabólicas na criança queimada"
                ]
            elif "Fraturas" in m["theme"]:
                m["theme"] = "Princípios Gerais de Fraturas e Osteossíntese"
                m["dbSubtemas"] = ["Princípios Gerais de Fraturas e Osteossíntese"]
                m["details"] = [
                    "Classificação geral das fraturas: fechadas vs expostas (Classificação de Gustilo-Anderson)",
                    "Manejo imediato das fraturas expostas: antibioticoterapia precoce, antitetânica e desbridamento",
                    "Métodos de imobilização e princípios de osteossíntese (estabilidade absoluta vs relativa)",
                    "Complicações das fraturas: pseudoartrose, retardo de consolidação e embolia gordurosa"
                ]

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print("Fixed remaining 2 Cirurgia themes!")
