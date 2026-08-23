import json
import sqlite3
import os

new_themes_list = json.load(open('clinica_summary.json', 'r', encoding='utf-8'))
new_themes = {t['name']: t for t in new_themes_list}

mapping = {
    'AVC e Doenças Cerebrovasculares': 'AVC',
    'Acidente Vascular Cerebral Isquêmico': 'AVC',
    'Anemias': 'Anemias e Hemoglobinopatias',
    'Arboviroses e Doenças Infecciosas Tropicais': 'Síndromes Febris',
    'Arritmias e Fibrilação Atrial': 'Arritmias, Síncope e PCR',
    'Artrites e Doenças Reumatológicas (AR, Gota, Osteoartrite)': 'Artrites e Diagnósticos Diferenciais',
    'Ascite - Diuréticos': 'Cirrose, Insuficiência Hepática e Complicações',
    'Asma': 'Distúrbios Obstrutivos',
    'Asma e DPOC': 'Distúrbios Obstrutivos',
    'Capnografia': 'Pneumointensivismo',
    'Cefaleias': 'Cefaleias',
    'Cirrose e Complicações': 'Cirrose, Insuficiência Hepática e Complicações',
    'DPOC': 'Distúrbios Obstrutivos',
    'Demências e Parkinson': 'Geriatria e Demências',
    'Dependência Química e Tabagismo': 'Abuso de Álcool, Tabaco e Outras Substâncias',
    'Dermatologia': 'Farmacodermias e Dermatoses',
    'Dermatologia (Lesões Cutâneas, Eczemas, Psoríase)': 'Farmacodermias e Dermatoses',
    'Derrame Pleural Complicado (Empiema)': 'Pneumonias e Síndromes Gripais',
    'Derrame Pleural e Doenças Pleurais': 'Doenças pulmonares intersticiais',
    'Diabetes Mellitus e Complicações': 'Diabetes',
    'Diabetes Mellitus e Complicações Agudas': 'Diabetes',
    'Dislipidemia e Risco Cardiovascular': 'Síndrome Metabólica e Dislipidemia',
    'Distúrbios Hidroeletrolíticos e Ácido-Base': 'Distúrbios Hidroeletrolíticos e Acidobásicos',
    'Distúrbios da Adrenal e Hipófise': 'Paratireoides, Suprarrenal e Outras Síndromes Endócrinas',
    'Distúrbios da Coagulação e Plaquetas': 'Distúrbios da Hemostasia, Desordens Trombóticas e Transfusão de Hemocomponentes',
    'Doença Inflamatória Intestinal e Diarreia Crônica': 'Síndromes Febris', # Fallback
    'Doença Renal Crônica': 'Insuficiência Renal',
    'Doenças Pulmonares Intersticiais': 'Doenças pulmonares intersticiais',
    'Doenças Pulmonares Intersticiais e Outras Pneumopatias': 'Doenças pulmonares intersticiais',
    'Doenças das Vias Biliares e Pâncreas': 'Cirrose, Insuficiência Hepática e Complicações',
    'Doenças do Esôfago e Estômago': 'Intoxicações Exógenas e Acidentes por Animais Peçonhentos', # Fallback
    'Doenças do Esôfago e Estômago (DRGE, Úlcera, Dispepsia)': 'Intoxicações Exógenas e Acidentes por Animais Peçonhentos',
    'Emergências Clínicas e Intoxicações': 'Intoxicações Exógenas e Acidentes por Animais Peçonhentos',
    'Endocardite Infecciosa': 'Endocardite e Infecção de Corrente Sanguínea',
    'Epilepsia e Doenças Neuromusculares': 'Síndromes Neurológicas e Fraqueza Muscular',
    'Geriatria e Cuidados Paliativos': 'Geriatria e Demências',
    'Glomerulopatias': 'Glomerulopatias e Tubulopatias',
    'Glomerulopatias e Síndrome Nefrítica/Nefrótica': 'Glomerulopatias e Tubulopatias',
    'HIV/AIDS e Infecções Oportunistas': 'HIV e AIDS no Adulto Não Gestante',
    'Hepatites Virais': 'Hepatites e Doenças do Metabolismo da Bilirrubina',
    'Hipertensão Arterial Sistêmica': 'Hipertensão Arterial Sistêmica',
    'Infecções de Pele e ISTs (Sífilis, Hanseníase, Micoses)': 'Infecções de Pele, Ossos e Partes Moles',
    'Injúria Renal Aguda': 'Insuficiência Renal',
    'Insuficiência Cardíaca': 'Insuficiência Cardíaca',
    'Leucemias e Linfomas': 'Onco-Hematologia',
    'Leucemias, Linfomas e Mieloma': 'Onco-Hematologia',
    'Litíase Urinária e Infecção Urinária': 'Insuficiência Renal',
    'Lúpus e Doenças Autoimunes Sistêmicas': 'Colagenoses e Miopatias',
    'Lúpus e Doenças Autoimunes Sistêmicas (Esclerose, Vasculites)': 'Vasculites',
    'Oftalmologia Clínica': 'Síndromes Neurológicas e Fraqueza Muscular', # Fallback
    'Oncologia (Rastreio e Neoplasias Sólidas)': 'Onco-Hematologia',
    'Oncologia e Neoplasias': 'Onco-Hematologia',
    'Osteoporose e Doença Óssea': 'Paratireoides, Suprarrenal e Outras Síndromes Endócrinas',
    'Osteoporose e Doença Óssea Metabólica': 'Paratireoides, Suprarrenal e Outras Síndromes Endócrinas',
    'Otorrinolaringologia': 'Pneumonias e Síndromes Gripais',
    'Parada Cardiorrespiratória e Suporte Avançado de Vida': 'Arritmias, Síncope e PCR',
    'Pericardiopatias': 'Insuficiência Cardíaca',
    'Pneumonia Adquirida na Comunidade': 'Pneumonias e Síndromes Gripais',
    'Pneumonia e Infecções Respiratórias': 'Pneumonias e Síndromes Gripais',
    'Pneumotórax Iatrogênico': 'Pneumointensivismo',
    'Radiografia de Tórax na Insuficiência Cardíaca': 'Insuficiência Cardíaca',
    'Sepse e Choque': 'Sepse, Choque Séptico e Outros tipos de Choque',
    'Síndromes Coronarianas Agudas': 'Síndrome Coronariana e Diagnósticos Diferenciais',
    'Síndromes Coronarianas Agudas (IAM e Angina)': 'Síndrome Coronariana e Diagnósticos Diferenciais',
    'Tireoidopatias': 'Tireoide',
    'Transtornos Psiquiátricos': 'Transtornos Mentais',
    'Transtornos Psiquiátricos (Depressão, Ansiedade, Psicoses)': 'Transtornos Mentais',
    'Tromboembolismo Venoso e TEP': 'Embolia Pulmonar e Hipertensão Pulmonar',
    'Tuberculose': 'Tuberculose',
    'Valvopatias': 'Valvopatias e Cardiomiopatias',
    'Ventilação Mecânica e Medicina Intensiva': 'Pneumointensivismo'
}

# Update plannerData.json
with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    planner_data = json.load(f)

for area in planner_data:
    if area['area'] == 'Clínica Médica':
        area['macroThemes'] = []
        for t in new_themes_list:
            area['macroThemes'].append({
                'theme': t['name'],
                'highYield': t['highYield'],
                'dbSubtemas': [t['name']]
            })

with open('app/backend/scripts/plannerData.json', 'w', encoding='utf-8') as f:
    json.dump(planner_data, f, indent=2, ensure_ascii=False)

# Update taxonomy.json
with open('app/backend/data/taxonomy.json', 'r', encoding='utf-8') as f:
    taxonomy = json.load(f)

for area in taxonomy:
    if area['area'] == 'Clínica Médica':
        area['macroThemes'] = []
        for t in new_themes_list:
            area['macroThemes'].append({
                'theme': t['name'],
                'highYield': t['highYield'],
                'dbSubtemas': [t['name']]
            })

with open('app/backend/data/taxonomy.json', 'w', encoding='utf-8') as f:
    json.dump(taxonomy, f, indent=2, ensure_ascii=False)

# Update katomartCourseDurations.json
with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    durations = json.load(f)

for t in new_themes_list:
    durations["subtemas"][t["name"]] = {
        "theory_hours": round(t["lesson_hours"], 2),
        "module": t["name"],
        "match_confidence": 1.0
    }

with open('app/backend/scripts/katomartCourseDurations.json', 'w', encoding='utf-8') as f:
    json.dump(durations, f, indent=2, ensure_ascii=False)

# Clean and Update subtema_map.json
with open('app/backend/data/subtema_map.json', 'r', encoding='utf-8') as f:
    smap = json.load(f)

valid_subtemas = set()
for area in taxonomy:
    for m in area['macroThemes']:
        valid_subtemas.update(m['dbSubtemas'])

# Allocate new IDs for CM
import re
cm_ids = [int(v.split('-')[1]) for v in smap.values() if v.startswith('CM-')]
next_id = max(cm_ids) + 1 if cm_ids else 1

for t in new_themes_list:
    if t["name"] not in smap:
        smap[t["name"]] = f"CM-{next_id:03d}"
        next_id += 1

new_map = {k: v for k, v in smap.items() if k in valid_subtemas}

with open('app/backend/data/subtema_map.json', 'w', encoding='utf-8') as f:
    json.dump(dict(sorted(new_map.items())), f, indent=2, ensure_ascii=False)

# Update SQLite DB
db_path = 'app/backend/medquest.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for old, new in mapping.items():
        if new in new_map:
            new_id = new_map[new]
            cur.execute("UPDATE questions SET subtema = ?, subtema_id = ? WHERE subtema = ?", (new, new_id, old))
            print(f"Updated DB: {old} -> {new} ({new_id})")
    conn.commit()
    conn.close()

print("Migration script completed!")
