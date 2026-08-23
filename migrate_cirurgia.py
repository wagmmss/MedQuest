import json
import os
import sqlite3

# Define the new themes from Medway (without "Como cai...")
# We will use these as both macroThemes and dbSubtemas for 1:1 mapping.
medway_focos_high_yield = [
    "Tumores do Aparelho Digestivo",
    "Abdome Agudo Inflamatório",
    "Trauma Abdominal",
    "Cuidados Pré-operatórios",
    "Cuidados e Complicações Pós-Operatórias",
    "Trauma Torácico",
    "Afecções Benignas das Vias Biliares",
    "Hérnias",
    "Abdome Agudo Obstrutivo",
    "Tumores Dermatológicos",
    "Abordagem Inicial (xABCDE)",
    "Feridas, Enxertos e Retalhos",
    "Cólon e Reto na cirurgia",
    "Cirurgia da Obesidade",
    "Cirurgia Pediátrica",
    "Hemorragia Digestiva"
]

mapping = {
  "Abdome Agudo Obstrutivo": "Abdome Agudo Obstrutivo",
  "Abdome Agudo Perfurativo": "Abdome Agudo Perfurativo",
  "Anestesiologia e Técnica Operatória": "Anestesia",
  "Aneurismas e Dissecção de Aorta": "Aneurismas",
  "Apendicite Aguda": "Abdome Agudo Inflamatório",
  "Atendimento Inicial ao Trauma (ATLS)": "Abordagem Inicial (xABCDE)",
  "Avaliação Pré-operatória e Risco Cirúrgico": "Cuidados Pré-operatórios",
  "Choque e Transfusão no Trauma": "Abordagem Inicial (xABCDE)",
  "Cirurgia Bariátrica e Complicações": "Cirurgia da Obesidade",
  "Cirurgia Pediátrica": "Cirurgia Pediátrica",
  "Cirurgia Torácica e Mediastino": "Cirurgia Torácica",
  "Cirurgia Vascular Periférica (Isquemia Arterial, Varizes, TVP)": "Doença arterial periférica",
  "Colecistite e Colelitíase": "Afecções Benignas das Vias Biliares",
  "Coledocolitíase e Colangite": "Afecções Benignas das Vias Biliares",
  "Câncer Colorretal": "Tumores do Aparelho Digestivo",
  "Diverticulite Aguda": "Abdome Agudo Inflamatório",
  "Doenças Orificiais (Hemorroida, Fissura, Fístula)": "Cólon e Reto na cirurgia",
  "Doenças do Esôfago (DRGE, Acalasia, Câncer)": "Síndrome Disfágica",
  "Estômago (Úlcera, HDA, Câncer Gástrico)": "Síndrome Dispéptica",
  "Hérnias da Parede Abdominal": "Hérnias",
  "Infecção de Sítio Cirúrgico e Cicatrização": "Cuidados e Complicações Pós-Operatórias",
  "Isquemia Mesentérica": "Abdome Agudo Isquêmico",
  "Neurocirurgia (Hemorragia, Hidrocefalia, Tumor)": "Trauma Cranioencefálico (TCE)",
  "Oftalmologia Cirúrgica": "Oftalmologia",
  "Ortopedia e Fraturas": "Fraturas Ósseas",
  "Otorrinolaringologia Cirúrgica": "Outras Afecções Cirúrgicas de Cabeça e Pescoço",
  "Pancreatite Aguda": "Afecções Pancreáticas",
  "Queimaduras": "Queimaduras",
  "Resposta Metabólica ao Trauma e Pós-operatório": "Cuidados e Complicações Pós-Operatórias",
  "Tireoide e Paratireoide": "Outras Afecções Cirúrgicas de Cabeça e Pescoço",
  "Trauma Abdominal": "Trauma Abdominal",
  "Trauma Cervical e Vascular": "Trauma de Face e Pescoço",
  "Trauma Cranioencefálico e Raquimedular": "Trauma Cranioencefálico (TCE)",
  "Trauma Pélvico e Urológico": "Trauma Abdominal",
  "Trauma Torácico": "Trauma Torácico",
  "Tumores de Pele e Partes Moles": "Tumores Dermatológicos",
  "Tumores de Pele e Partes Moles (Melanoma, CBC, CEC)": "Tumores Dermatológicos",
  "Urologia (Litíase, HPB, Neoplasia Renal, Escroto Agudo)": "Afecções Urológicas Benignas"
}

with open('cirurgia_summary.json', 'r', encoding='utf-8') as f:
    cirurgia_summary = json.load(f)

# Collect the base themes, accumulating lesson_hours for "Como cai..."
new_themes = {}
for theme in cirurgia_summary:
    name = theme['name']
    base_name = name
    if "Como cai" in name:
        base_name = name.split(": ")[-1]
        
    if base_name not in new_themes:
        new_themes[base_name] = {
            "name": base_name,
            "lesson_hours": 0.0,
            "highYield": base_name in medway_focos_high_yield
        }
    new_themes[base_name]["lesson_hours"] += theme["lesson_hours"]
    # If the sub-theme is high yield, mark base as high yield
    if name in medway_focos_high_yield:
         new_themes[base_name]["highYield"] = True

# Now generate the macroThemes for plannerData.json and taxonomy.json
macro_themes = []
for t in new_themes.values():
    macro_themes.append({
        "theme": t["name"],
        "highYield": t["highYield"],
        "dbSubtemas": [t["name"]],
        "details": ["Tema Medway."]
    })

# Read taxonomy.json
with open('app/backend/data/taxonomy.json', 'r', encoding='utf-8') as f:
    taxonomy = json.load(f)
for area in taxonomy:
    if area["area"] == "Cirurgia" or area["area"] == "Cirurgia Geral":
        area["macroThemes"] = macro_themes

with open('app/backend/data/taxonomy.json', 'w', encoding='utf-8') as f:
    json.dump(taxonomy, f, indent=2, ensure_ascii=False)

# Read plannerData.json
with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    planner_data = json.load(f)
for area in planner_data:
    if area["area"] == "Cirurgia Geral":
        area["macroThemes"] = macro_themes

with open('app/backend/scripts/plannerData.json', 'w', encoding='utf-8') as f:
    json.dump(planner_data, f, indent=2, ensure_ascii=False)

# Update subtema_map.json
with open('app/backend/data/subtema_map.json', 'r', encoding='utf-8') as f:
    subtema_map = json.load(f)

current_cir_id = max([int(v.split('-')[1]) for k, v in subtema_map.items() if v.startswith("CIR-")])
for t in new_themes.keys():
    if t not in subtema_map:
        current_cir_id += 1
        subtema_map[t] = f"CIR-{current_cir_id:03d}"

with open('app/backend/data/subtema_map.json', 'w', encoding='utf-8') as f:
    # write sorted
    sorted_map = dict(sorted(subtema_map.items()))
    json.dump(sorted_map, f, indent=2, ensure_ascii=False)

# Update katomartCourseDurations.json
with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    course_durations = json.load(f)

# we need to remove old surgery subtemas from durations, or just update/add the new ones
# Let's just add the new ones, overriding old if they overlap
for t in new_themes.values():
    course_durations["subtemas"][t["name"]] = {
        "theory_hours": round(t["lesson_hours"], 2),
        "module": t["name"],
        "match_confidence": 1.0
    }

with open('app/backend/scripts/katomartCourseDurations.json', 'w', encoding='utf-8') as f:
    json.dump(course_durations, f, indent=2, ensure_ascii=False)

# Update DB
db_path = 'app/backend/medquest.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for old_name, new_name in mapping.items():
        if old_name != new_name:
            new_id = subtema_map.get(new_name)
            if new_id:
                print(f"Updating DB: {old_name} -> {new_name} ({new_id})")
                cur.execute("UPDATE questions SET subtema = ?, subtema_id = ? WHERE subtema = ?", (new_name, new_id, old_name))
    conn.commit()
    conn.close()
    print("DB migration complete.")
else:
    print(f"DB not found at {db_path}")

print("Migration script completed!")
