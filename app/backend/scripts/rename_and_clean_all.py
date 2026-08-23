import json
import sqlite3

# Load current taxonomy
with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

# Name mapping dictionary from old Medway literal name to new professional medical theme name
RENAMING = {
    # --- MEDICINA PREVENTIVA ---
    "Ética médica, Bioética e Documentação": "Ética Médica, Bioética e Prontuários / Documentos",
    "Estudos Epidemiológicos (Análise Estatística e Aplicação)": "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística",
    "Estudos Epidemiológicos (Classificação)": "Delineamentos e Classificação dos Estudos Epidemiológicos",
    "Indicadores de Morbimortalidade": "Indicadores de Saúde e Coeficientes de Morbimortalidade",
    "Perfis e Indicadores demográficos": "Transição Demográfica e Perfis Populacionais",
    "Níveis de Prevenção": "História Natural da Doença e Níveis de Prevenção",
    "Aspectos Históricos do SUS": "História das Políticas de Saúde e Origens do SUS",
    "A Evolução do SUS": "Legislação, Diretrizes e Evolução do SUS",
    "Atenção Primária à Saúde": "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)",
    "Estatística de Testes Diagnósticos": "Avaliação de Testes Diagnósticos e Curva ROC",
    "Epidemias, Endemias e Pandemias": "Vigilância Epidemiológica: Endemias, Epidemias e Surtos",
    "Notificação": "Vigilância em Saúde e Notificação Compulsória (SINAN)",
    "Vigilância em Saúde do Trabalhador": "Saúde do Trabalhador e Doenças Ocupacionais",

    # --- PEDIATRIA ---
    "Desordens do Sistema Imune": "Imunodeficiências, Alergias e Anafilaxia na Infância",
    "Cardiopatias Congênitas": "Cardiopatias Congênitas Cianogênicas e Acianogênicas",
    "Arritmias, Síncope e PCR": "Arritmias, Síncope e Parada Cardiorrespiratória Pediátrica",
    "Constipação Intestinal": "Constipação Intestinal Funcional e Orgânica",
    "Síndromes Diarreicas e Disabsortivas": "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas",
    "Desordens Genéticas e Erros Inatos do Metabolismo": "Genética Médica, Cromossomopatias e Erros Inatos do Metabolismo",
    "Infecção do Trato Urinário (ITU)": "Infecção do Trato Urinário (ITU) e Refluxo Vesicoureteral na Infância",
    "Doenças Exantemáticas": "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas",
    "Imunizações": "Calendário Vacinal do PNI e Imunizações Especiais",
    "Parasitoses": "Parasitoses Intestinais: Helmintíases e Protozooses",
    "Período Neonatal: Doenças Hematológicas": "Neonatologia: Icterícia Neonatal e Doenças Hematológicas",
    "Período Neonatal: Doenças Infecciosas": "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal",
    "Período Neonatal: Doenças do Metabolismo": "Neonatologia: Distúrbios Metabólicos e Hipoglicemia no Recém-Nascido",
    "Período Neonatal: Doenças Respiratórias": "Neonatologia: Desconforto Respiratório e Doença da Membrana Hialina",
    "Período Neonatal: Doenças Neurológicas e Sensoriais": "Neonatologia: Asfixia Perinatal, Encefalopatia e Doenças Neurológicas",
    "Sala de Parto": "Reanimação Neonatal e Assistência em Sala de Parto",
    "Alojamento Conjunto e Testes de Triagem Neonatal": "Alojamento Conjunto e Testes de Triagem Neonatal (Pezinho, Olhinho, Coraçãozinho)",
    "Epilepsia e Síndromes Convulsivas": "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância",
    "Distúrbios Carenciais": "Anemias Carenciais e Distúrbios de Micronutrientes (Ferro, Vitamina D)",
    "Nutrição na Pediatria": "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil",
    "Nariz, Ouvido e Laringe": "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite",
    "Distúrbios Obstrutivos": "Asma na Infância, Bronquiolite Viral Aguda e Laringites",
    "Segurança e Violência na Infância": "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos",
    "Avaliação e Transtornos do Comportamento na Infância e Adolescência": "Transtornos do Neurodesenvolvimento (TEA, TDAH) e Saúde Mental na Infância",
    "Distúrbios Estaturais e Puberais": "Baixa Estatura, Puberdade Precoce e Atraso Puberal",
    "Crescimento e Desenvolvimento na Infância e Adolescência": "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento",
    "Sepse, Choque Séptico e Outros tipos de Choque": "Reconhecimento da Sepse e Manejo do Choque Pediátrico",
    "Vasculites": "Vasculites na Infância: Púrpura de Henoch-Schönlein e Doença de Kawasaki",

    # --- GINECOLOGIA E OBSTETRÍCIA ---
    "Tumores do colo uterino": "Câncer de Colo Uterino e Lesões Precursoras",
    "Pré-Natal": "Assistência Pré-Natal de Baixo e Alto Risco",
    "Rastreamento do Câncer de Colo Uterino": "Rastreamento Citopatológico e Conduta em Lesões Cervicais (HPV)",
    "Doenças do Corpo Uterino e Endométrio": "Afecções do Corpo Uterino, Endométrio e Sangramento Pós-Menopausa",
    "Diabetes mellitus na gravidez": "Diabetes Gestacional e Pré-Gestacional",
    "Outras doenças na gestação": "Condições Clínicas Intercorrentes na Gravidez",
    "Síndromes Hipertensivas da Gestação": "Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)",
    "Hepatites virais, HIV/AIDS e outras infecções na gestação": "Infecções Perinatais e Transmissão Vertical (HIV, Sífilis, Hepatites, EGB)",
    "Ciclo Menstrual": "Fisiologia do Ciclo Menstrual e Eixo Hipotálamo-Hipófise-Ovário",
    "Contracepção": "Métodos Contraceptivos: Hormonais, DIU e Cirúrgicos",
    "Climatério": "Climatério, Menopausa e Terapia de Reposição Hormonal (TRH)",
    "Amenorreias e Síndrome dos Ovários Policísticos": "Investigação das Amenorreias e Síndrome dos Ovários Policísticos (SOP)",
    "Anatomia Pélvica": "Anatomia Cirúrgica e Estruturas Pélvicas Femininas",
    "Dor pélvica crônica": "Endometriose, Adenomiose e Dor Pélvica Crônica",
    "Doença Inflamatória Pélvica e Violência Sexual": "Doença Inflamatória Pélvica (DIP) e Atendimento à Violência Sexual",
    "Vulvovaginites": "Vulvovaginites e Diagnóstico Diferencial dos Corrimentos Vaginais",
    "Infertilidade conjugal": "Investigação e Propêdêutica da Infertilidade Conjugal",
    "Doenças Benignas da Mama": "Mastologia Benigna: Fibroadenomas, Cistos e Mastites",
    "Tumores Malignos da Mama": "Câncer de Mama: Rastreamento, Diagnóstico e Estadiamento",
    "Medicina Fetal": "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade",
    "Tumores dos Ovários": "Massas Anexiais e Neoplasias Ovarianas",
    "Estática fetal, Pelve e Mecanismo de Parto": "Bacia Obstétrica, Estática Fetal e Mecanismo do Parto",
    "Assistência ao Parto": "Assistência Clínica ao Trabalho de Parto, Partograma e Distocias",
    "Rotura Prematura de Membranas Ovulares e Infecção Ovular": "Amniorrexe Prematura (RPMO) e Corioamnionite",
    "Trabalho de parto prematuro": "Trabalho de Parto Prematuro e Tocólise",
    "Puerpério": "Puerpério Fisiológico, Patológico e Hemorragia Pós-Parto",
    "Sangramento da Primeira Metade da Gestação": "Hemorragias da Primeira Metade: Abortamento, Ectópica e Mola",
    "Sangramento da Segunda Metade da Gestação": "Hemorragias da Segunda Metade: Placenta Prévia e DPP",
    "PALM-COEIN": "Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose",
    "Sofrimento Fetal": "Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal",
    "Úlceras genitais": "Úlceras Genitais e Infecções Sexualmente Transmissíveis na Mulher",
    "Incontinência Urinária e Prolapsos de Órgãos Pélvicos": "Uroginecologia: Incontinência Urinária e Prolapso Genital",
    "Patologias da Vulva e Vagina": "Patologias Benignas e Neoplásicas da Vulva e Vagina",
    "Conceitos em sexualidade": "Fundamentos em Sexualidade Humana e Saúde Reprodutiva",
    "Disfunções sexuais": "Disfunções Sexuais Femininas e Dispareunia",
    "Fístulas": "Fístulas Urogenitais e Retovaginais",
    "Morte materna": "Causas de Mortalidade Materna e Estratégias de Redução",

    # --- CLÍNICA MÉDICA ---
    "Saúde Mental no Brasil": "Políticas de Saúde Mental e Atenção Psicossocial (CAPS)",
    "Arritmias, Síncope e PCR": "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)",
    "Valvopatias e Cardiomiopatias": "Valvopatias Adquiridas e Miocardiopatias",
    "Hipertensão Arterial Sistêmica": "Hipertensão Arterial Sistêmica e Crises Hipertensivas",
    "Insuficiência Cardíaca": "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica",
    "Síndrome Coronariana e Diagnósticos Diferenciais": "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)",
    "Farmacodermias e Dermatoses": "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase",
    "Doenças Infectoparasitárias com Acometimento Dermatológico": "Dermatoses Infecciosas, Hanseníase e Leishmanioses",
    "Paratireoides, Suprarrenal e Outras Síndromes Endócrinas": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
    "Tireoide": "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos",
    "Diabetes": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
    "Síndrome Metabólica e Dislipidemia": "Dislipidemias, Síndrome Metabólica e Risco Cardiovascular",
    "Geriatria e Demências": "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas",
    "Cirrose, Insuficiência Hepática e Complicações": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
    "Hepatites e Doenças do Metabolismo da Bilirrubina": "Hepatites Virais (A, B, C) e Icterícias Metabólicas",
    "Infecções do Sistema Nervoso Central": "Meningites, Encefalites e Infecções do SNC",
    "Tuberculose": "Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo",
    "Pneumonias e Síndromes Gripais": "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas",
    "Doenças Sexualmente Transmissíveis": "Infecções Sexualmente Transmissíveis (ISTs) no Adulto",
    "Infecções de Pele, Ossos e Partes Moles": "Celulite, Erisipela, Osteomielite e Infecções de Partes Moles",
    "Endocardite e Infecção de Corrente Sanguínea": "Endocardite Infecciosa e Sepse de Foco Endovascular",
    "HIV e AIDS no Adulto Não Gestante": "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas",
    "Síndromes Febris": "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)",
    "Glomerulopatias e Tubulopatias": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
    "Distúrbios Hidroeletrolíticos e Acidobásicos": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
    "Insuficiência Renal": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
    "Cefaleias": "Cefaleias Primárias (Enxaqueca, Tensional) e Secundárias de Alarme",
    "Síndromes Neurológicas e Fraqueza Muscular": "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares",
    "Neurointensivismo e Ética Médica": "Neurointensivismo, Morte Encefálica e Cuidados Críticos",
    "AVC": "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)",
    "Distúrbios da Hemostasia, Desordens Trombóticas e Transfusão de Hemocomponentes": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
    "Onco-Hematologia": "Leucemias, Linfomas e Mieloma Múltiplo",
    "Anemias e Hemoglobinopatias": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
    "Embolia Pulmonar e Hipertensão Pulmonar": "Tromboembolismo Pulmonar (TEP) e Hipertensão Pulmonar",
    "Distúrbios Obstrutivos": "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)",
    "Doenças pulmonares intersticiais": "Doenças Pulmonares Intersticiais e Fibrose Pulmonar",
    "Transtornos Mentais": "Psiquiatria: Transtornos do Humor, Ansiedade e Psicoses",
    "Abuso de Álcool, Tabaco e Outras Substâncias": "Transtornos por Uso de Substâncias (Álcool, Tabaco e Drogas de Abuso)",
    "Artrites e Diagnósticos Diferenciais": "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas",
    "Colagenoses e Miopatias": "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias",
    "Vasculites": "Vasculites Sistêmicas dos Grandes, Médios e Pequenos Vasos",
    "Sepse, Choque Séptico e Outros tipos de Choque": "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica",
    "Pneumointensivismo": "Ventilação Mecânica, SARA e Insuficiência Respiratória Aguda",
    "Intoxicações Exógenas e Acidentes por Animais Peçonhentos": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",

    # --- CIRURGIA GERAL ---
    "Abdome Agudo Inflamatório": "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)",
    "Abdome Agudo Isquêmico": "Abdome Agudo Vascular e Isquemia Mesentérica",
    "Abdome Agudo Obstrutivo": "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)",
    "Abdome Agudo Perfurativo": "Abdome Agudo Perfurativo e Úlcera Péptica Perfurada",
    "Abordagem Inicial (xABCDE)": "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)",
    "Afecções Benignas das Vias Biliares": "Litíase Biliar, Colecistite, Coledocolitíase e Colangite",
    "Afecções Pancreáticas": "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos",
    "Afecções Urológicas Benignas": "Hiperplasia Prostática Benigna (HPB) e Litíase Urinária",
    "Anestesia": "Fundamentos da Anestesiologia, Farmacologia e Bloqueios",
    "Aneurismas": "Aneurismas de Aorta Abdominal e Torácica",
    "Cirurgia da Obesidade": "Cirurgia Bariátrica e Metabólica",
    "Cirurgia Pediátrica": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
    "Cirurgia Torácica": "Cirurgia Torácica Geral e Doenças Pleurais",
    "Cólon e Reto na cirurgia": "Coloproctologia: Doenças Orificiais e Afecções Colorretais",
    "Cuidados e Complicações Pós-Operatórias": "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas",
    "Doença Inflamatória Intestinal": "Abordagem Cirúrgica das Doenças Inflamatórias Intestinais (Crohn e RCU)",
    "Cuidados Pré-operatórios": "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico",
    "Doença arterial periférica": "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas",
    "Doenças Venosas": "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)",
    "Feridas, Enxertos e Retalhos": "Cicatrização, Tratamento de Feridas, Enxertos e Retalhos",
    "Técnica Operatória": "Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)",
    "Hemorragia Digestiva": "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica",
    "Hérnias": "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)",
    "Queimaduras": "Atendimento ao Paciente Queimado e Reposição Volêmica",
    "Como cai na PED: Queimaduras": "Particularidades das Queimaduras na Faixa Etária Pediátrica",
    "Síndrome Disfágica": "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica",
    "Síndrome Dispéptica": "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica",
    "Trauma Abdominal": "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)",
    "Trauma Cranioencefálico (TCE)": "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana",
    "Trauma de Face e Pescoço": "Trauma Cervical e Fraturas Maxilofaciais",
    "Trauma Torácico": "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco",
    "Tumores Dermatológicos": "Oncologia Cutânea: Melanoma, CBC e CEC",
    "Tumores do Aparelho Digestivo": "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)",
    "Tumores Urológicos": "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo",
    "Fraturas Ósseas": "Princípios Gerais de Fraturas e Osteossíntese",
    "Ortopedia Pediátrica": "Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise",
    "Luxações/ Lesões Ligamentares": "Luxações Articulares e Lesões Ligamentares / Meniscais",
    "Tendinites/ Tenossinovites/ Fasceítes e Bursites": "Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética",
    "Tumores Ortopédicos": "Neoplasias Ósseas Benignas e Sarcomas Ósseos",
    "Tumores Pulmonares e Do Mediastino": "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino",
    "Cirurgia Cardíaca": "Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar",
    "Outras Afecções Cirurgicas de Cabeça e Pescoço": "Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos",
    "Tumores de partes moles": "Sarcomas de Partes Moles",
    "Oftalmologia": "Emergências Oftalmológicas e Patologias Oculares Frequentes",
    "Polipose intestinal": "Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias",
    "Trauma da Coluna Vertebral (TRM)": "Trauma Raquimedular (TRM) e Lesões Vertebrais",
    "Trauma de membros e extremidades": "Trauma Ortopédico de Extremidades e Síndrome Compartimental",
    "Tumores de Cabeça e Pescoço": "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos"
}

# 1. Update taxonomy.json
for area_data in tax:
    for macro in area_data.get("macroThemes", []):
        old_theme = macro.get("theme")
        new_theme = RENAMING.get(old_theme, old_theme)
        macro["theme"] = new_theme
        macro["dbSubtemas"] = [new_theme]
        # Clean details from any explicit mentions of Medway
        new_details = []
        for d in macro.get("details", []):
            d_clean = d.replace("Medway.", "").replace("Tema Medway.", "").replace("Medway", "").strip()
            if d_clean:
                new_details.append(d_clean)
        if not new_details:
            new_details = [new_theme]
        macro["details"] = new_details

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print("Updated taxonomy.json with new refined theme names and removed Medway mentions!")

# 2. Update katomartCourseDurations.json
with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

new_subs = {}
for old_name, val in kat.get("subtemas", {}).items():
    new_name = RENAMING.get(old_name, old_name)
    val["module"] = new_name
    new_subs[new_name] = val

kat["subtemas"] = new_subs
with open("app/backend/scripts/katomartCourseDurations.json", "w", encoding="utf-8") as f:
    json.dump(kat, f, ensure_ascii=False, indent=2)

print("Updated katomartCourseDurations.json with new theme names!")

# 3. Update medquest.db questions subtema
conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row
questions = conn.execute("SELECT id, subtema FROM questions").fetchall()

db_updates = []
for q in questions:
    old_sub = q["subtema"]
    new_sub = RENAMING.get(old_sub, old_sub)
    if new_sub != old_sub:
        db_updates.append((new_sub, q["id"]))

print(f"Applying {len(db_updates)} subtema name updates to medquest.db...")
if db_updates:
    conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", db_updates)
    conn.commit()

print("All questions updated in medquest.db!")
