import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

with open("go_plan_compiled.json", "r", encoding="utf-8") as f:
    go_plan = json.load(f)

# Built detailed curriculum descriptions for the 37 Medway GO modules
module_details = {
    "Tumores do colo uterino": [
        "Câncer de colo uterino: epidemiologia, tipos histológicos (epidermoide, adenocarcinoma)",
        "Estadiamento clínico FIGO e exames de imagem complementares",
        "Tratamento cirúrgico (conização, traquilectomia, histerectomia radical/Wertheim-Meigs) vs Radioquimioterapia",
        "Seguimento oncológico e recidivas"
    ],
    "Pré-Natal": [
        "Assistência pré-natal de baixo risco: calendário de consultas e rotina de exames laboratoriais/ultrassonográficos",
        "Suplementação de ácido fólico e sulfato ferroso; vacinação da gestante (dTpa, Hepatite B, Influenza, dT)",
        "Cálculo da idade gestacional e data provável do parto (regra de Naegele)",
        "Avaliação nutricional, ganho de peso e rastreamento de estreptococo do grupo B (EGB)"
    ],
    "Rastreamento do Câncer de Colo Uterino": [
        "Diretrizes brasileiras do Ministério da Saúde e INCA para rastreamento citopatológico (Papanicolaou)",
        "História natural da infecção pelo HPV, vacinação e lesões precursoras (LIEBG, LIEAG, ASC-US, ASC-H, AGC)",
        "Indicações e achados de colposcopia (zona de transformação, teste de Schiller, ácido acético)",
        "Condutas diagnósticas e terapêuticas (repetição citológica, biópsia dirigida, CAF/EZT)"
    ],
    "Doenças do Corpo Uterino e Endométrio": [
        "Hiperplasia endometrial com e sem atipias: classificação OMS, fatores de risco e conduta",
        "Câncer de endométrio: tipos histológicos (tipo I estrogênio-dependente vs tipo II), fatores de risco e diagnóstico",
        "Estadiamento FIGO e princípios do tratamento cirúrgico e adjuvante",
        "Sarcomas uterinos e tumores estromais"
    ],
    "Diabetes mellitus na gravidez": [
        "Rastreamento e critérios diagnósticos de Diabetes Mellitus Gestacional (DMG) e Diabetes Overt (pré-gestacional)",
        "Metas glicêmicas e controle com dieta, atividade física e insulinoterapia",
        "Repercussões maternas e fetais (macrossomia, polidramnia, hipoglicemia neonatal, malformações)",
        "Conduta obstétrica, via de parto e reavaliação puerperal (TOTG 75g 6 semanas pós-parto)"
    ],
    "Outras doenças na gestação": [
        "Isoimunização Rh: fisiopatologia, Coombs indireto, profilaxia com imunoglobulina anti-D e conduta na gestante sensibilizada",
        "Trombofilias hereditárias e adquiridas (SAF) na gestação: anticoagulação e desfechos gestacionais",
        "Cardiopatias e nefropatias na gravidez: estratificação de risco materno",
        "Anemias carenciais e hemoglobinopatias na gestação"
    ],
    "Síndromes Hipertensivas da Gestação": [
        "Classificação: Hipertensão Arterial Crônica, Pré-Eclâmpsia, Eclâmpsia e Hipertensão Gestacional",
        "Critérios de gravidade da pré-eclâmpsia e síndrome HELLP",
        "Manejo farmacológico anti-hipertensivo e prevenção de eclâmpsia com Sulfato de Magnésio (esquemas de Pritchard e Zuspan)",
        "Conduta obstétrica, timing do parto e profilaxia com AAS e cálcio em gestantes de alto risco"
    ],
    "Hepatites virais, HIV/AIDS e outras infecções na gestação": [
        "Manejo do HIV na gestação: TARV combinada, profilaxia da transmissão vertical, via de parto conforme carga viral e manejo do RN",
        "Hepatites B e C na gestação: rastreamento, imunoprofilaxia no neonato e profilaxia com Tenofovir",
        "Infecções congênitas (STORCH: Sífilis, Toxoplasmose, Rubéola, CMV, Herpes e Zika)",
        "Diagnóstico materno, tratamento intrauterino e acompanhamento fetal"
    ],
    "Ciclo Menstrual": [
        "Fisiologia do eixo hipotálamo-hipófise-ovariano e esteroidogênese ovariana",
        "Fase folicular, pico de LH/ovulação e fase lútea do ciclo ovariano",
        "Modificações endometriais: fases proliferativa, secretora e menstrual",
        "Ação dos estrogênios e progestagênios sobre muco cervical e órgãos-alvo"
    ],
    "Contracepção": [
        "Critérios Médicos de Elegibilidade da OMS para Uso de Métodos Anticoncepcionais (Categorias 1 a 4)",
        "Métodos reversíveis de longa duração (LARC): DIU de cobre, DIU com levonorgestrel e implante subdérmico",
        "Contraceptivos hormonais combinados (orais, injetáveis, anel vaginal, adesivo) e de progestagênio isolado",
        "Contracepção de emergência e métodos cirúrgicos definitivos (laqueadura tubária e vasectomia)"
    ],
    "Climatério": [
        "Fisiopatologia da transição menopáusica e pós-menopausa",
        "Quadro clínico: sintomas vasomotores, síndrome geniturinária da menopausa, osteoporose e risco cardiovascular",
        "Terapia de Reposição Hormonal (TRH): indicações, contraindicações formais, regimes terapêuticos e janela de oportunidade",
        "Alternativas não hormonais para manejo dos sintomas vasomotores"
    ],
    "Amenorreias e Síndrome dos Ovários Policísticos": [
        "Investigação sistemática de amenorreia primária (avaliação de genitália, cariótipo, FSH, LH) e amenorreia secundária",
        "Testes diagnósticos funcionais: teste da progesterona, teste do estrogênio + progesterona, dosagens hormonais",
        "Síndrome dos Ovários Policísticos (SOP): critérios diagnósticos de Rotterdam, fisiopatologia da resistência insulínica",
        "Manejo clínico da SOP: hiperandrogenismo, irregularidade menstrual e infertilidade"
    ],
    "Anatomia Pélvica": [
        "Anatomia cirúrgica da pelve feminina: órgãos genitais internos, vascularização e inervação",
        "Assoalho pélvico: diafragma pélvico (músculo elevador do ânus) e diafragma urogenital",
        "Ligamentos de sustentação e suspensão uterina (uterossacros, cardinais/Mackenrodt, redondos e largos)",
        "Relações anatômicas do trajeto ureteral na pelve e prevenção de lesões iatrogênicas"
    ],
    "Dor pélvica crônica": [
        "Diagnóstico diferencial de dor pélvica crônica e dismenorreia secundária",
        "Endometriose: teorias etiopatogênicas, apresentações clínicas (peritoneal, ovariana/endometrioma, profunda)",
        "Diagnóstico por imagem (USG com preparo intestinal, RNM) e estadiamento",
        "Tratamento clínico hormonal e indicações de abordagem cirúrgica laparoscópica"
    ],
    "Doença Inflamatória Pélvica e Violência Sexual": [
        "Doença Inflamatória Pélvica (DIP): etiologia polimicrobiana (N. gonorrhoeae, C. trachomatis, anaeróbios), critérios diagnósticos e estadiamento de Monif",
        "Tratamento ambulatorial vs hospitalar da DIP e complicações (abscesso tubo-ovariano, síndrome de Fitz-Hugh-Curtis)",
        "Atendimento integral à vítima de violência sexual: acolhimento humanizado, profilaxias pós-exposição (PEP HIV, ISTs não virais, hepatite B) e contracepção de emergência",
        "Aspectos legais, notificação compulsória e aborto previsto em lei"
    ],
    "Vulvovaginites": [
        "Ecossistema vaginal normal e diagnóstico diferencial dos corrimentos genitais",
        "Vaginose bacteriana: critérios de Amsel e Nugent, diagnóstico microscópico e tratamento",
        "Candidíase vulvovaginal: fatores de risco, apresentações clínicas (complicada vs não complicada) e esquemas antifúngicos",
        "Tricomoníase: manifestações clínicas, achados colposcópicos ('colo em framboesa') e tratamento do casal"
    ],
    "Infertilidade conjugal": [
        "Definição, epidemiologia e propedêutica básica do casal infértil (fator ovulatório, tuboperitoneal, uterino e masculino)",
        "Interpretação do espermograma e histerossalpingografia",
        "Avaliação da reserva ovariana (FSH basal, contagem de folículos antrais, hormônio antimülleriano)",
        "Princípios de tratamentos de baixa e alta complexidade (indução de ovulação, inseminação intrauterina, FIV/ICSI)"
    ],
    "Doenças Benignas da Mama": [
        "Anomalias do desenvolvimento mamário e dor mamária (mastalgia cíclica vs acíclica)",
        "Doenças inflamatórias e infecciosas: mastite puerperal, abscesso mamário e mastite periductal",
        "Tumores benignos comuns: fibroadenoma, cistos mamários simples, papiloma intraductal e tumor filodes",
        "Fluxo papilar: classificação (água de rocha, sanguinolento, lácteo) e conduta investigativa"
    ],
    "Tumores Malignos da Mama": [
        "Câncer de mama: fatores de risco genéticos (BRCA1, BRCA2) e ambientais",
        "Rastreamento mamográfico (diretrizes Ministério da Saúde vs SBM/CBR) e classificação BI-RADS",
        "Biópsias mamárias (core biopsy, mamotomia, biópsia cirúrgica) e subtipos moleculares (Luminal A, Luminal B, HER2+, Triplo-negativo)",
        "Princípios do tratamento cirúrgico conservador vs mastectomia, biópsia do linfonodo sentinela e terapias sistêmicas/adjuvantes"
    ],
    "Medicina Fetal": [
        "Rastreamento ultrassonográfico do primeiro trimestre (translucência nucal, osso nasal, ducto venoso)",
        "Diagnóstico de malformações congênitas e métodos invasivos de diagnóstico genético (biópsia de vilo corial, amniocentese)",
        "Restrição de Crescimento Fetal (RCF/CIUR): classificação em precoce vs tardio e diagnóstico diferencial com feto PIG constitucional",
        "Gestação múltipla/gemelaridade: determinação de zigocidade e corionicidade, complicações específicas (STFF, TAPS)"
    ],
    "Tumores dos Ovários": [
        "Abordagem da massa anexial: diferenciação entre cistos funcionais e neoplasias ovarianas",
        "Marcadores tumorais séricos (CA-125, CEA, alfafetoproteína, beta-hCG) e critérios ultrassonográficos IOTA de malignidade",
        "Câncer de ovário: tipos histológicos (epitelial seroso de alto grau, mucinoso, células germinativas, estroma do cordão sexual)",
        "Estadiamento FIGO e princípios da cirurgia citorredutora e quimioterapia"
    ],
    "Estática fetal, Pelve e Mecanismo de Parto": [
        "Estática fetal: atitude, situação, apresentação e posição fetal",
        "Estudo da bacia obstétrica (estreito superior, médio e inferior) e tipos de pelve (ginecoide, androide, antropoide, platipeloide)",
        "Tempos do mecanismo de parto em apresentação cefálica fletida: insinuação, descida, flexão, rotação interna, desprendimento e rotação externa",
        "Diagnóstico de variedades de posição e assinclitismo (Litzmann, Nagele)"
    ],
    "Assistência ao Parto": [
        "Períodos clínicos do parto: dilatação, expulsivo, delivramento e período de Greenberg",
        "Preenchimento e interpretação do partograma: linhas de alerta e ação, distócias funcionais (fase ativa prolongada, parada secundária da dilatação/descida)",
        "Boas práticas de assistência ao parto humanizado e indicações formais de cesariana",
        "Parto instrumentalizado (fórcipe de Simpson e Kielland, vácuo-extrator) e manejo do 3º e 4º períodos (prevenção ativa de hemorragia puerperal)"
    ],
    "Rotura Prematura de Membranas Ovulares e Infecção Ovular": [
        "Rotura Prematura de Membranas Ovulares (RPMO): diagnóstico clínico e testes confirmatórios (teste da nitrazina, cristalização, USG)",
        "Conduta conforme idade gestacional: termo vs pré-termo (corticoide, antibioticoprofilaxia de latência)",
        "Corioamnionite clínica: critérios diagnósticos de Gibbs, antibióticos terapêuticos e indicação de resolução da gestação",
        "Rastreamento e profilaxia intraparto para Estreptococo do Grupo B (EGB)"
    ],
    "Trabalho de parto prematuro": [
        "Trabalho de Parto Prematuro (TPP): fatores de risco, diagnóstico clínico e marcadores preditivos (medida do colo uterino por USG TV, fibronectina fetal)",
        "Tocólise: indicações, contraindicações e drogas de escolha (bloqueadores dos canais de cálcio, antagonistas da ocitocina, AINEs)",
        "Corticoterapia antenatal para aceleração da maturidade pulmonar fetal (Betametasona / Dexametasona)",
        "Neuroproteção fetal com Sulfato de Magnésio em gestações < 32 semanas"
    ],
    "Puerpério": [
        "Fisiologia do puerpério imediato, tardio e remoto: involução uterina e loquiação normal",
        "Hemorragia pós-parto (HPP): regra dos 4 Ts (Tônus, Trauma, Tecido, Trombina), diagnóstico e estadiamento de choque",
        "Medidas medicamentosas (Ocitocina, Misoprostol, Ácido Tranexâmico), balão de tamponamento intrauterino e técnicas cirúrgicas",
        "Infecção puerperal / Endometrite: fatores de risco, diagnóstico e esquema antibiótico (Clindamicina + Gentamicina)"
    ],
    "Sangramento da Primeira Metade da Gestação": [
        "Abortamento: formas clínicas (ameaça, completo, incompleto, retido, infectado, habitual) e esvaziamento uterino (AMIU vs curetagem)",
        "Gravidez Ectópica: fatores de risco, apresentações clínicas, diagnóstico por USG TV + beta-hCG seriado e condutas (expectante, Metotrexato, salpingostomia/salpingectomia)",
        "Doença Trofoblástica Gestacional: mola hidatiforme completa vs parcial, dosagem de beta-hCG e seguimento pós-molar",
        "Diagnóstico diferencial com lesões cervicais e cervicites hemorrágicas"
    ],
    "Sangramento da Segunda Metade da Gestação": [
        "Descolamento Prematuro de Placenta (DPP): fatores de risco, tríade clássica (dor abdominal súbita, hipertonia uterina, sangramento escuro) e conduta de emergência",
        "Placenta Prévia: classificação, quadro clínico (sangramento indolor, rutilante, recidivante) e via de parto",
        "Rotura de Vasa Prévia: diagnóstico clínico (sangramento e sofrimento fetal agudo pós-amniotomia)",
        "Rotura Uterina: sinais de iminência (sinal de Bandl-Frommel) e rotura consumada"
    ],
    "PALM-COEIN": [
        "Classificação FIGO para Sangramento Uterino Anormal (SUA): causas estruturais (Pólipo, Adenomiose, Leiomioma, Malignidade) e não estruturais (Coagulopatia, Ovulatória, Endometrial, Iatrogênica, Não classificada)",
        "Miomatose uterina: classificação topográfica (submucoso, intramural, subseroso), manifestações clínicas e opções terapêuticas",
        "Adenomiose: fisiopatologia, diagnóstico por imagem e tratamento",
        "Abordagem diagnóstica e condutas clínicas/cirúrgicas no SUA agudo e crônico"
    ],
    "Sofrimento Fetal": [
        "Sofrimento fetal agudo intraparto: avaliação da vitalidade fetal",
        "Cardiotocografia intraparto: análise da linha de base, variabilidade, acelerações e desacelerações (DIP I precoce, DIP II tardio, DIP III variável)",
        "Classificação dos traçados cardiotocográficos nas categorias I, II e III do ACOG/FIGO",
        "Perfil Biofísico Fetal (PBF) e medidas de reanimação intrauterina e resolução do parto"
    ],
    "Úlceras genitais": [
        "Abordagem sindrômica e etiológica das úlceras genitais",
        "Sífilis primária (cancro duro) e secundária: diagnóstico laboratorial (testes treponêmicos e não treponêmicos) e tratamento com Penicilina Benzatina",
        "Herpes genital: apresentações primária e recorrente, diagnóstico clínico e tratamento com antiviral (Aciclovir)",
        "Cancro mole, Linfogranuloma venéreo e Donovanose: agentes causais e opções terapêuticas"
    ],
    "Incontinência Urinária e Prolapsos de Órgãos Pélvicos": [
        "Incontinência urinária de esforço (IUE) vs Incontinência urinária de urgência (IUU) / Bexiga hiperativa",
        "Avaliação clínica, diário miccional e estudo urodinâmico (pressão de perda ao esforço, cistometria)",
        "Tratamento conservador (fisioterapia pélvica, antimuscarínicos, beta-3 agonistas) e cirúrgico (slings sintéticos)",
        "Prolapso de órgãos pélvicos: estadiamento POP-Q e condutas clínicas (pessários) e cirúrgicas"
    ],
    "Patologias da Vulva e Vagina": [
        "Dermatoses vulvares não neoplásicas: líquen escleroso, líquen plano e líquen simples crônico",
        "Neoplasia Intraepitelial Vulvar (NIV) e Neoplasia Intraepitelial Vaginal (NIVA): diagnóstico e manejo",
        "Câncer de vulva: fatores de risco, histologia e estadiamento",
        "Patologias benignas da glândula de Bartholin: cisto e abscesso (marsupialização e bartolinectomia)"
    ],
    "Conceitos em sexualidade": [
        "Resposta sexual humana e modelos do ciclo de resposta sexual",
        "Conceitos fundamentais de sexo biológico, identidade de gênero e orientação sexual",
        "Abordagem e anamnese da saúde sexual no consultório ginecológico",
        "Aspectos psicossociais e relacionais da sexualidade"
    ],
    "Disfunções sexuais": [
        "Classificação das disfunções sexuais femininas: transtorno do desejo/interesse sexual hipoativo, transtorno da excitação, transtorno do orgasmo",
        "Transtornos de dor gênito-pélvica/penetração: vaginismo e dispareunia",
        "Etiologias orgânicas, hormonais, farmacológicas e psicogênicas",
        "Estratégias de intervenção clínica multidisciplinar e sexologia médica"
    ],
    "Fístulas": [
        "Fístulas urogenitais e retogenitais: etiologia obstétrica (trabalho de parto obstruído prolongado) vs cirúrgica/iatrogênica",
        "Quadro clínico: perda urinária ou fecal contínua pela vagina e dermatite associada",
        "Propedêutica diagnóstica: teste dos três tampões, cistoscopia, vaginoscopia e exames de imagem contrastados",
        "Princípios do tratamento cirúrgico reparador e momento ideal para intervenção"
    ],
    "Morte materna": [
        "Conceito e definição de morte materna segundo a CID-10 (direta vs indireta)",
        "Cálculo e interpretação da Razão de Mortalidade Materna (RMM)",
        "Principais causas de mortalidade materna no Brasil: síndromes hipertensivas, hemorragias, infecções e abortamento",
        "Papel dos Comitês de Prevenção da Mortalidade Materna e estratégias de redução da morbimortalidade materna"
    ]
}

# Build the 37 macro-themes
new_go_macro = []
for item in go_plan:
    name = item["name"]
    high_yield = item["high_yield"]
    details = module_details.get(name, [name])
    
    new_go_macro.append({
        "theme": name,
        "highYield": high_yield,
        "dbSubtemas": [name],
        "details": details
    })

# Find Ginecologia e Obstetrícia area in taxonomy
go_index = -1
for i, area_data in enumerate(taxonomy):
    area_name = area_data.get("area", "")
    if "Ginecologia" in area_name or "Obstetr" in area_name:
        go_index = i
        break

if go_index >= 0:
    taxonomy[go_index]["macroThemes"] = new_go_macro
    print(f"Replaced Ginecologia e Obstetrícia with {len(new_go_macro)} Medway macro-themes!")
else:
    taxonomy.append({
        "area": "Ginecologia e Obstetrícia",
        "macroThemes": new_go_macro
    })
    print("Added Ginecologia e Obstetrícia to taxonomy!")

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(taxonomy, f, ensure_ascii=False, indent=2)

print("Saved updated taxonomy.json!")
