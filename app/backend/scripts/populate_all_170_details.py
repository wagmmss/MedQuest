import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

# Comprehensive detailed pedagogical checklist items for all Cirurgia and Clinica Medica modules
DETAILS_MAP = {
    # ==================== CIRURGIA GERAL (48 MODULOS) ====================
    "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)": [
        "Apendicite aguda: fisiopatologia, escores clínicos (Alvarado) e diagnóstico por imagem (USG e TC)",
        "Apendicite aguda: conduta cirúrgica (laparoscopia vs aberta) e manejo de complicações (abscesso e peritonite)",
        "Diverticulite aguda de cólon: classificação de Hinchey e indicações de tratamento clínico vs cirúrgico",
        "Diagnósticos diferenciais do abdome agudo inflamatório na urgência"
    ],
    "Abdome Agudo Vascular e Isquemia Mesentérica": [
        "Isquemia mesentérica aguda: oclusão arterial embólica vs trombose venosa mesentérica",
        "Quadro clínico, diagnóstico precoce por angiotomografia e metas de revascularização",
        "Isquemia mesentérica crônica (angina mesentérica) e colite isquêmica"
    ],
    "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)": [
        "Fisiopatologia da obstrução mecânica alta (delgado) vs baixa (cólon)",
        "Obstrução por bridas/aderências: manejo conservador vs cirúrgico",
        "Volvo de sigmoide e ceco: descompressão endoscópica vs ressecção cirúrgica",
        "Obstrução em alça fechada, estrangulamento e sinais de isquemia"
    ],
    "Abdome Agudo Perfurativo e Úlcera Péptica Perfurada": [
        "Causas de perfuração do trato gastrointestinal alto e baixo",
        "Identificação de pneumoperitônio ao raio-x e tomografia computadorizada",
        "Manejo cirúrgico de úlcera péptica perfurada: sutura, epiploplastia (Patch de Graham)"
    ],
    "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)": [
        "Protocolo ATLS 10ª edição: controle de hemorragia exsanguinante (X) e via aérea com proteção cervical (A)",
        "Respiração e ventilação (B): identificação de pneumotórax hipertensivo e hemotórax maciço",
        "Circulação e choque (C): classes de choque hemorrágico e protocolo de transfusão maciça",
        "Avaliação neurológica (D) pela escala de Glasgow-P e exposição com controle de hipotermia (E)"
    ],
    "Litíase Biliar, Colecistite, Coledocolitíase e Colangite": [
        "Colelitíase assintomática e cólica biliar: indicações de colecistectomia profilática",
        "Colecistite aguda calculosa e acalculosa: critérios de Tokyo e tempo ideal para colecistectomia",
        "Coledocolitíase: estratificação de risco (CPRE pré-operatória vs exploração cirúrgica da via biliar)",
        "Colangite aguda: tríade de Charcot, pêntade de Reynolds e drenagem biliar de urgência"
    ],
    "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos": [
        "Pancreatite aguda: critérios de Atlanta (leve, moderada e grave) e escores prognósticos (Ranson/BISAP)",
        "Suporte clínico: hidratação guiada por metas, analgesia e nutrição enteral precoce",
        "Complicações locais: coleções fluidas, necrose pancreática infectada (Step-up approach)",
        "Pancreatite crônica: etiologia, insuficiência exócrina/endócrina e pseudocistos"
    ],
    "Hiperplasia Prostática Benigna (HPB) e Litíase Urinária": [
        "HPB: quadro clínico de LUTS, IPSS e tratamento clínico (alfa-bloqueadores e inibidores de 5-alfa-redutase)",
        "Indicações de tratamento cirúrgico na HPB (RTUP, prostatectomia aberta e laser)",
        "Litíase urinária: propedêutica na cólica nefrética aguda e critérios de intervenção urológica (LEOC, URS)"
    ],
    "Fundamentos da Anestesiologia, Farmacologia e Bloqueios": [
        "Avaliação do risco anestésico (Classificação ASA e Mallampati)",
        "Bloqueios neuroaxiais: raquianestesia vs anestesia peridural e suas contraindicações",
        "Farmacologia dos hipnóticos, opioides e bloqueadores neuromusculares",
        "Hipertermia maligna: fisiopatologia, diagnóstico precoce e reversão com Dantroleno"
    ],
    "Aneurismas de Aorta Abdominal e Torácica": [
        "Aneurisma de Aorta Abdominal (AAA): história natural, rastreamento e indicações de correção eletiva",
        "Ruptura de AAA: apresentação clínica, choque hemorrágico e protocolo de reparo de urgência (EVAR vs aberta)",
        "Dissecção aguda de aorta: classificação de Stanford (A vs B) e diretrizes terapêuticas"
    ],
    "Cirurgia Bariátrica e Metabólica": [
        "Critérios de indicação e contraindicações para cirurgia bariátrica (CFM e SBCBM)",
        "Principais técnicas cirúrgicas: Bypass Gástrico em Y de Roux vs Gastrectomia Vertical (Sleeve)",
        "Complicações precoces e tardias: fístulas, embolia pulmonar, deficiências nutricionais e síndrome de Dumping"
    ],
    "Cirurgia Pediátrica e Malformações Digestivas Neonatais": [
        "Atresia de esôfago e fístula traqueoesofágica: diagnóstico e manejo inicial",
        "Estenose hipertrófica do piloro: alcalose hipoclorêmica e piloromiotomia de Ramstedt",
        "Hérnia diafragmática congênita, gastrosquise e onfalocele",
        "Enterocolite necrosante neonatal: critérios de Bell e indicações cirúrgicas"
    ],
    "Cirurgia Torácica Geral e Doenças Pleurais": [
        "Drenagem pleural tubular fechada: técnica, posicionamento do dreno e sistema de selo d'água",
        "Empiema pleural: fases evolutivas (exsudativa, fibrinopurulenta e organizada) e decorticação",
        "Pneumotórax espontâneo primário e secundário: indicações de pleurodese e ressecção de bolhas"
    ],
    "Coloproctologia: Doenças Orificiais e Afecções Colorretais": [
        "Doença hemorroidária interna e externa: estadiamento e opções terapêuticas (ligadura elástica vs hemorroidectomia)",
        "Fissura anal crônica: fisiopatologia, esfincterotomia interna e bloqueadores de canais de cálcio tópicos",
        "Abscesso e fístula anorretal: classificação de Parks, colocação de sedenho e fístulectomia",
        "Doença pilonidal sacrococcígea e prolapso retal"
    ],
    "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas": [
        "Resposta metabólica e endócrina ao trauma cirúrgico (REMIT)",
        "Febre no pós-operatório: regra dos 5 'W' (Wind, Water, Wound, Walking, Wonder drugs)",
        "Complicações da ferida operatória: seroma, hematoma, infecção do sítio cirúrgico (ISC) e deiscência",
        "Íleo paralítico pós-operatório vs obstrução mecânica precoce"
    ],
    "Abordagem Cirúrgica das Doenças Inflamatórias Intestinais (Crohn e RCU)": [
        "Retocolite Ulcerativa: manifestações colônicas, colite fulminante, megacólon tóxico e proctocolectomia total",
        "Doença de Crohn: acometimento transmural, fístulas, estenoses e cirurgia poupadora (estrituroplastia)",
        "Rastreamento e vigilância de displasia e câncer colorretal nas DIIs"
    ],
    "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico": [
        "Anamnese pré-operatória e solicitação racional de exames laboratoriais complementares",
        "Avaliação de risco cardiovascular: escore de Goldman, índice de Lee (RCRI) e diretrizes da SBC",
        "Avaliação de risco pulmonar, renal e hepático (escore de Child-Pugh e MELD)",
        "Manejo pré-operatório de medicações crônicas: anticoagulantes, antiagregantes e hipoglicemiantes"
    ],
    "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas": [
        "Oclusão arterial aguda: os 6 'P' (Pain, Pallor, Pulselessness, Paresthesia, Paralysis, Poikilothermia) e Fogarty",
        "Doença Arterial Obstrutiva Periférica (DAOP): claudicação, índice tornozelo-braquial (ITB) e Fontaine/Rutherford",
        "Isquemia crítica de membros e opções de revascularização (endovascular vs pontes venosas)"
    ],
    "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)": [
        "Varizes de membros inferiores e insuficiência venosa crônica: classificação CEAP e condutas",
        "Trombose Venosa Profunda (TVP): Tríade de Virchow, escore de Wells e ultrassonografia doppler",
        "Profilaxia mecânica e farmacológica de tromboembolismo venoso (TEV) no paciente cirúrgico"
    ],
    "Cicatrização, Tratamento de Feridas, Enxertos e Retalhos": [
        "Fases da cicatrização tecidual: hemostasia, inflamação, proliferação e remodelação",
        "Cicatrização patológica: cicatriz hipertrófica vs queloide",
        "Princípios de enxertia de pele (espessura parcial vs total) e retalhos cutâneos/faciocutâneos"
    ],
    "Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)": [
        "Paramentação cirúrgica, degermação, antissepsia e campos operatórios estéreis",
        "Instrumental cirúrgico fundamental: pinças hemostáticas, tesouras, bisturis e afastadores",
        "Fios cirúrgicos absorvíveis (Catgut, Vicryl, PDS) e inabsorvíveis (Nylon, Seda, Prolene)",
        "Tipos de pontos e técnicas de sutura na síntese tecidual"
    ],
    "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica": [
        "HDA não varicosa: úlcera péptica, classificação de Forrest e hemostasia endoscópica",
        "HDA varicosa: manejo da hipertensão portal, terlipressina, ligadura elástica e TIPS",
        "HDB: divertículos, angiodisplasias, colonoscopia e arteriografia"
    ],
    "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)": [
        "Anatomia da região inguinal: canal inguinal, trígono de Hesselbach e orifício de Fruchaud",
        "Hérnia inguinal indireta vs direta: classificação de Nyhus e diagnóstico clínico",
        "Técnicas de correção sem tensão: técnica de Lichtenstein e laparoscopia (TAPP/TEP)",
        "Hérnias femorais, umbilicais, epigástricas e hérnias incisionais"
    ],
    "Atendimento ao Paciente Queimado e Reposição Volêmica": [
        "Classificação da profundidade (1º, 2º e 3º graus) e cálculo da extensão pela Regra dos Nove de Wallace",
        "Ressuscitação volêmica nas primeiras 24 horas: Fórmula de Parkland e débito urinário alvo",
        "Critérios de internação em Centro de Queimados (CTQ) e indicações de escarotomia/fasciotomia"
    ],
    "Particularidades das Queimaduras na Faixa Etária Pediátrica": [
        "Cálculo de área queimada em crianças (Tabela de Lund-Browder)",
        "Reposição volêmica na criança com fórmula de Parkland associada a glicosado de manutenção",
        "Prevenção de hipotermia, analgesia e complicações metabólicas na criança queimada"
    ],
    "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica": [
        "Acalásia e megaesôfago chagásico: fisiopatologia, esofagograma e manometria de alta resolução",
        "Classificação de Rezende e opções de tratamento (Cardiomiotomia a Heller com fundoplicatura e POEM)",
        "Espasmo esofagiano difuso, esôfago em quebra-nozes e divertículo de Zenker"
    ],
    "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica": [
        "DRGE: manifestações típicas e atípicas, endoscopia digestiva alta e pHmetria de 24h",
        "Complicações da DRGE: esofagite erosiva (Los Angeles), estenose péptica e Esôfago de Barrett",
        "Cirurgia antirrefluxo: indicações e técnica da Fundoplicatura de Nissen (360°)"
    ],
    "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)": [
        "Avaliação no trauma abdominal fechado: estabilidade hemodinâmica, FAST/E-FAST e TC",
        "Indicações formais de laparotomia imediata no paciente hemodinamicamente instável",
        "Trauma penetrante por arma branca e de fogo: exploração local vs laparotomia mandatória",
        "Manejo do trauma esplênico e hepático: conduta não operatória (CNO) vs tratamento cirúrgico"
    ],
    "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana": [
        "Classificação do TCE pela escala de Glasgow (Leve: 13-15, Moderado: 9-12, Grave: 3-8)",
        "Indicações de tomografia de crânio no TCE leve (Regras de New Orleans e Canadian CT)",
        "Lesões intracranianas focais: Hematoma Epidural (biconvexo) vs Hematoma Subdural (crescente)",
        "Medidas clínicas e cirúrgicas para controle da Hipertensão Intracraniana (HIC)"
    ],
    "Trauma Cervical e Fraturas Maxilofaciais": [
        "Anatomia cirúrgica do pescoço: Zonas I, II e III cervicais e indicações cirúrgicas",
        "Lesões da via aérea, esôfago e grandes vasos no trauma cervical penetrante",
        "Fraturas de face: classificação de Le Fort (I, II e III), fratura de mandíbula e Blowout orbitário"
    ],
    "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco": [
        "Pneumotórax hipertensivo: diagnóstico clínico imediato, descompressão e drenagem torácica",
        "Pneumotórax aberto: curativo de 3 pontas e drenagem em selo d'água",
        "Hemotórax maciço: critérios diagnósticos e indicações formais de toracotomia de urgência",
        "Tamponamento cardíaco: Tríade de Beck, FAST pericárdico e toracotomia / pericardiocentese"
    ],
    "Oncologia Cutânea: Melanoma, CBC e CEC": [
        "Carcinoma Basocelular (CBC): formas clínicas, fatores de risco e margens cirúrgicas",
        "Carcinoma Espinocelular (CEC): lesões precursoras (ceratose actínica) e abordagem cirúrgica",
        "Melanoma cutâneo: regra do ABCDE, biópsia excisional, níveis de Breslow e margens cirúrgicas",
        "Indicações de biópsia do linfonodo sentinela no melanoma"
    ],
    "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)": [
        "Câncer de esôfago: subtipos histológicos (CEC vs Adenocarcinoma), estadiamento e esofagectomia",
        "Câncer gástrico: classificação de Lauren (Intestinal vs Difuso), estadiamento e linfadenectomia a D2",
        "Adenocarcinoma de pâncreas: sinal de Courvoisier-Terrier, estadiamento e cirurgia de Whipple",
        "Câncer colorretal: rastreamento populacional, colonoscopia, estadiamento e colectomias oncológicas"
    ],
    "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo": [
        "Câncer de próstata: rastreamento com PSA e toque retal, biópsia transretal e escore de Gleason / ISUP",
        "Câncer renal: carcinoma de células claras, tríade clássica e nefrectomia parcial vs radical",
        "Câncer de bexiga: fatores de risco (tabagismo), hematúria indolor e ressecção transuretral (RTU)",
        "Tumores testiculares: marcadores tumorais (alfa-fetoproteína, beta-hCG, DHL) e orquiectomia inguinal"
    ],
    "Princípios Gerais de Fraturas e Osteossíntese": [
        "Classificação geral das fraturas: fechadas vs expostas (Classificação de Gustilo-Anderson)",
        "Manejo imediato das fraturas expostas: antibioticoterapia precoce, antitetânica e desbridamento",
        "Métodos de imobilização e princípios de osteossíntese (estabilidade absoluta vs relativa)",
        "Complicações das fraturas: pseudoartrose, retardo de consolidação e embolia gordurosa"
    ],
    "Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise": [
        "Displasia do Desenvolvimento do Quadril (DDQ): manobras de Ortolani e Barlow e suspensório de Pavlik",
        "Sinovite transitória do quadril vs Artrite séptica pediátrica (critérios de Kocher)",
        "Epifisiólise proximal do fêmur em adolescentes e doença de Legg-Calvé-Perthes"
    ],
    "Luxações Articulares e Lesões Ligamentares / Meniscais": [
        "Luxação glenoumeral anterior: mecanismo, redução incruenta e complicações do nervo axilar",
        "Lesões ligamentares do joelho: Ligamento Cruzado Anterior (LCA), teste de Lachman e gaveta anterior",
        "Lesões meniscais e luxações traumáticas de cotovelo e quadril"
    ],
    "Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética": [
        "Síndrome do manguito rotador: tendinopatia do supraespinhal, testes de Neer e Hawkins",
        "Epicondilite lateral (cotovelo de tenista) e medial (cotovelo de golfista)",
        "Tenossinovite de De Quervain (teste de Finkelstein) e fasceíte plantar"
    ],
    "Neoplasias Ósseas Benignas e Sarcomas Ósseos": [
        "Tumores ósseos benignos mais comuns: osteocondroma, encondroma e osteoma osteoide",
        "Sarcomas ósseos primários: Osteossarcoma (reação periosteal em raio de sol / triângulo de Codman)",
        "Sarcoma de Ewing (imagem em casca de cebola) em crianças e adolescentes"
    ],
    "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino": [
        "Nódulo Pulmonar Solitário (NPS): critérios radiológicos de benignidade vs malignidade",
        "Câncer de pulmão: tipos histológicos (Não Pequenas Células vs Pequenas Células) e ressecabilidade",
        "Tumores do mediastino: compartimentos mediastinais e os 4 'T' do mediastino anterior"
    ],
    "Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar": [
        "Cirurgia de Revascularização do Miocárdio (CRM): indicações e enxertos (mamária e safena)",
        "Princípios da Circulação Extracorpórea (CEC) e proteção miocárdica (cardioplegia)",
        "Cirurgia de troca valvar e plastia valvar mitral/aórtica: próteses mecânicas vs biológicas"
    ],
    "Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos": [
        "Diagnóstico diferencial de massas cervicais: congênitas, inflamatórias e neoplásicas",
        "Cisto do ducto tireoglosso (Cirurgia de Sistrunk) e cisto da fenda branquial",
        "Afecções das glândulas salivares: sialolitíase, adenoma pleomórfico e tumor de Warthin"
    ],
    "Sarcomas de Partes Moles": [
        "Apresentação clínica de massas em partes moles: critérios de suspeição para malignidade",
        "Diagnóstico histopatológico por biópsia por agulha grossa (Core biopsy)",
        "Estadiamento, ressecção cirúrgica com margens tridimensionais livres e radioterapia adjuvante"
    ],
    "Emergências Oftalmológicas e Patologias Oculares Frequentes": [
        "Diagnóstico diferencial de olho vermelho na emergência: conjuntivite, ceratite, uveíte e glaucoma agudo",
        "Glaucoma agudo de ângulo fechado: apresentação clínica e tratamento medicamentoso de urgência",
        "Traumatismos oculares: perfuração ocular, hifema e queimaduras químicas",
        "Descolamento de retina e oclusões vasculares retinianas agudas"
    ],
    "Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias": [
        "Polipose Adenomatosa Familiar (PAF): mutação no gene APC e indicação de colectomia profilática",
        "Síndrome de Lynch (Câncer Colorretal Hereditário Não Polipoide): critérios de Amsterdã e Bethesda",
        "Síndrome de Peutz-Jeghers e Síndrome de Cowden: vigilância e seguimento oncológico"
    ],
    "Trauma Raquimedular (TRM) e Lesões Vertebrais": [
        "Avaliação neurológica sistemática: Escala da ASIA e determinação do nível motor/sensitivo",
        "Choque neurogênico (hipotensão e bradicardia) vs Choque medular (arreflexia transitória)",
        "Princípios de imobilização, critérios para imagem cervical (NEXUS e Canadian C-Spine) e descompressão"
    ],
    "Trauma Ortopédico de Extremidades e Síndrome Compartimental": [
        "Síndrome compartimental aguda: os 5 'P', aferição de pressão e indicação de fasciotomia",
        "Luxações do joelho e lesão da artéria poplítea: estratificação com índice tornozelo-braquial",
        "Fraturas de bacia: classificação de Tile/Young-Burgess, sangramento e fixação externa"
    ],
    "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos": [
        "Carcinoma Espinocelular (CEC) de cabeça e pescoço: fatores de risco e esvaziamentos cervicais",
        "Avaliação de nódulos tireoidianos: classificação ACR TI-RADS e indicações de PAAF",
        "Conduta no resultado citopatológico de PAAF de tireoide pela Classificação de Bethesda",
        "Câncer de tireoide bem diferenciado (Papilífero e Folicular) vs Medular e Anaplásico"
    ],

    # ==================== CLÍNICA MÉDICA (44 MODULOS) ====================
    "Políticas de Saúde Mental e Atenção Psicossocial (CAPS)": [
        "História da Reforma Psiquiátrica Brasileira e Lei 10.216/2001 (Lei Antimanicomial)",
        "Rede de Atenção Psicossocial (RAPS): Centros de Atenção Psicossocial (CAPS I, II, III, AD, i)",
        "Manejo de crises em saúde mental e urgências psiquiátricas na atenção primária e emergência",
        "Princípios de desinstitucionalização e reinserção psicossocial"
    ],
    "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)": [
        "Taquiarritmias de QRS estreito e largo: condutas com paciente estável vs instável (cardioversão elétrica)",
        "Bradiarritmias: BAV de 1º, 2º (Mobitz I e II) e 3º grau (BAVT) e indicações de marcapasso",
        "Algoritmos de Parada Cardiorrespiratória (PCR): ritmos chocáveis (FV/TVSP) vs não chocáveis (AESP/Assistolia)",
        "Etiologia e propedêutica da síncope: neuromediada, ortostática e cardiogênica"
    ],
    "Valvopatias Adquiridas e Miocardiopatias": [
        "Estenose e Insuficiência Mitral: sopros característicos, história natural e critérios de intervenção",
        "Estenose e Insuficiência Aórtica: tríade clássica da estenose aórtica e indicações cirúrgicas/TAVI",
        "Miocardiopatia Hipertrófica, Dilatada e Restritiva: diagnóstico e prevenção de morte súbita",
        "Miocardiopatia Chagásica: manifestações arrítmicas, insuficiência cardíaca e aneurisma apical"
    ],
    "Hipertensão Arterial Sistêmica e Crises Hipertensivas": [
        "Diagnóstico e estadiamento da HAS: critérios de consultório, MAPA e MRPA",
        "Estratificação de risco cardiovascular e metas pressóricas segundo as diretrizes brasileiras",
        "Tratamento medicamentoso inicial: IECA/BRA, bloqueadores de canais de cálcio e tiazídicos",
        "Crise hipertensiva: diferenciação entre Urgência Hipertensiva vs Emergência Hipertensiva"
    ],
    "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica": [
        "Fisiopatologia, critérios diagnósticos de Framingham e estadiamento (NYHA e estágios A-D)",
        "IC com fração de ejeção reduzida (ICFEr): quarteto fantástico (IECA/BRA/ARNI, BB, ARM e iSGLT2)",
        "Insuficiência Cardíaca Descompensada: perfis hemodinâmicos de Stevenson (A, B, C, L)",
        "Insuficiência Cardíaca com Fração de Ejeção Preservada (ICFEp): diagnóstico e manejo"
    ],
    "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)": [
        "Infarto com Supra de ST (IAMCSST): tempo porta-agulha, fibrinólise vs angioplastia primária (porta-balão)",
        "Síndrome Coronariana Aguda sem Supra de ST (SCASSST): estratificação de risco (escores GRACE e TIMI)",
        "Terapia anti-isquêmica, antiplaquetária dupla e anticoagulação plena na fase aguda",
        "Diagnóstico diferencial de dor torácica na sala de emergência"
    ],
    "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase": [
        "Farmacodermias graves: Síndrome de Stevens-Johnson (SSJ), NET e Síndrome DRESS",
        "Eczemas: dermatite atópica, dermatite de contato alérgica e irritativa",
        "Psoríase vulgar e artropatia psoriásica: fisiopatologia e opções terapêuticas tópicas e sistêmicas",
        "Lesões elementares em dermatologia e diagnóstico diferencial das dermatoses eritematodescamativas"
    ],
    "Dermatoses Infecciosas, Hanseníase e Leishmanioses": [
        "Hanseníase: formas clínicas (paucibacilar vs multibacilar), testes de sensibilidade e esquema PQT-U",
        "Reações hansênicas: Reação Tipo 1 (reversa) e Reação Tipo 2 (Eritema Nodoso Hansênico)",
        "Leishmaniose Tegumentar Americana (LTA): quadro cutâneo e mucoso, diagnóstico e tratamento",
        "Micoses superficiais e profundas: esporotricose e paracoccidioidomicose"
    ],
    "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio": [
        "Hiperparatireoidismo primário e secundário: fisiopatologia, diagnóstico e hipercalcemia",
        "Manejo da crise hipercalcêmica e hipocalcemia sintomática",
        "Síndrome de Cushing: rastreamento laboratorial e diagnóstico etiológico",
        "Insuficiência adrenal primária (Doença de Addison) vs secundária e manejo da crise adrenal aguda"
    ],
    "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos": [
        "Hipotireoidismo primário, subclínico e Tireoidite de Hashimoto: diagnóstico e reposição de levotiroxina",
        "Hipertireoidismo e Doença de Graves: quadro clínico, diagnóstico e drogas antitireoidianas (Metimazol/PTU)",
        "Crise tireotóxica e coma mixedematoso: reconhecimento e tratamento de emergência",
        "Tireoidites subagudas e crônicas: formas dolorosas vs indolores"
    ],
    "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento": [
        "Critérios diagnósticos de Diabetes Mellitus e pré-diabetes segundo a SBD/ADA",
        "Tratamento farmacológico do DM2: Metformina, iSGLT2, análogos de GLP-1, sulfonilureias e DPP-4",
        "Insulinoterapia no DM1 e DM2: esquemas basal-bolus e ajuste de doses",
        "Complicações crônicas: nefropatia, retinopatia, neuropatia diabética e pé diabético",
        "Complicações agudas: Cetoacidose Diabética (CAD) e Estado Hiperglicêmico Hiperosmolar (EHH)"
    ],
    "Dislipidemias, Síndrome Metabólica e Risco Cardiovascular": [
        "Classificação laboratorial das dislipidemias e metas de LDL-colesterol por estratificação de risco",
        "Terapia hipolipemiante: estatinas de alta potência, Ezetimiba e inibidores da PCSK9",
        "Síndrome metabólica: critérios diagnósticos (NCEP-ATP III e IDF) e intervenções no estilo de vida",
        "Manejo das hipertrigliceridemias graves e prevenção de pancreatite aguda"
    ],
    "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas": [
        "Avaliação Geriátrica Ampla (AGA): capacidade funcional (ABVD e AIVD), fragilidade e sarcopenia",
        "Síndromes demenciais: Doença de Alzheimer, Demência Vascular, Corpos de Lewy e Frontotemporal",
        "Diagnóstico diferencial de declínio cognitivo: Demência vs Delirium vs Depressão",
        "Instabilidade postural, prevenção de quedas no idoso e polifarmácia (Critérios de Beers)"
    ],
    "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática": [
        "Fisiopatologia da cirrose, estadiamento prognóstico (Escores de Child-Pugh e MELD)",
        "Síndrome de hipertensão portal: formação de ascite e circulação colateral",
        "Peritonite Bacteriana Espontânea (PBE): diagnóstico no líquido ascítico e antibioticoterapia",
        "Encefalopatia hepática, Síndrome Hepatorrenal e hemorragia por varizes de esôfago"
    ],
    "Hepatites Virais (A, B, C) e Icterícias Metabólicas": [
        "Hepatite A e E: transmissão fecal-oral, história natural e prevenção",
        "Hepatite B: interpretação sorológica completa (HBsAg, Anti-HBc, HBeAg, Anti-HBs) e indicações de tratamento",
        "Hepatite C: diagnóstico por sorologia e PCR (HCV-RNA) e novos antivirais de ação direta (DAA)",
        "Distúrbios do metabolismo da bilirrubina: Síndrome de Gilbert, Crigler-Najjar e Dubin-Johnson"
    ],
    "Meningites, Encefalites e Infecções do SNC": [
        "Meningite bacteriana aguda: etiologia por faixa etária, punção lombar e análise do líquor",
        "Antibioticoterapia empírica imediata e uso de Dexametasona adjuvante",
        "Quimioprofilaxia de contatos para meningococo e Haemophilus influenzae",
        "Encefalites virais (Herpes Simplex vírus), abscesso cerebral e neurocriptococose"
    ],
    "Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo": [
        "Tuberculose pulmonar: quadro clínico, radiografia de tórax e teste rápido molecular (TRM-TB) / BAAR",
        "Esquema de tratamento padrão: RIPE (Rifampicina, Isoniazida, Pirazinamida e Etambutol)",
        "Manejo de efeitos adversos dos tuberculostáticos e toxicidade hepática",
        "Tuberculose latente (ILTB): indicação de PPD/IGRA e quimioprofilaxia",
        "Formas extrapulmonares: pleural, meníngea e ganglionar"
    ],
    "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas": [
        "Agentes etiológicos típicos e atípicos da PAC em adultos",
        "Estratificação de gravidade e local de tratamento: escore CURB-65 e PSI",
        "Esquemas antimicrobianos empíricos ambulatoriais, em enfermaria e em UTI",
        "Complicações da pneumonia: derrame pleural parapneumônico e empiema",
        "Síndromes gripais, Influenza e COVID-19 grave"
    ],
    "Infecções Sexualmente Transmissíveis (ISTs) no Adulto": [
        "Sífilis adquirida: estágios primário, secundário, latente e terciário e tratamento com Penicilina Benzatina",
        "Interpretação de testes treponêmicos e não treponêmicos (VDRL) e controle de cura",
        "Uretrites infecciosas: Gonococo e Clamídia (diagnóstico e tratamento empírico combinado)",
        "Úlceras genitais: cancro mole, herpes genital, linfogranuloma venéreo e donovanose"
    ],
    "Celulite, Erisipela, Osteomielite e Infecções de Partes Moles": [
        "Diagnóstico diferencial entre erisipela (estreptocócica) e celulite infecciosa (estafilocócica)",
        "Fasceíte necrotizante e infecções graves de partes moles: reconhecimento e desbridamento de urgência",
        "Osteomielite no adulto: patogênese, diagnóstico por imagem e antibioticoterapia prolongada",
        "Artrite séptica aguda em articulações nativas: artrocentese e manejo"
    ],
    "Endocardite Infecciosa e Sepse de Foco Endovascular": [
        "Critérios diagnósticos de Duke modificados para Endocardite Infecciosa",
        "Etiologias microbianas: S. aureus, Estreptococos do grupo viridans e Enterococos",
        "Indicações de ecocardiograma transtorácico e transesofágico",
        "Esquemas antibióticos prolongados e indicações cirúrgicas de urgência",
        "Profilaxia de endocardite infecciosa em procedimentos odontológicos"
    ],
    "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas": [
        "Fluxograma diagnóstico de HIV pelo Ministério da Saúde e monitoramento de CD4/Carga Viral",
        "Terapia Antirretroviral (TARV) inicial: esquemas preferenciais (DTG + TDF + 3TC)",
        "Profilaxia Pré-Exposição (PrEP) e Pós-Exposição (PEP)",
        "Principais infecções oportunistas: Pneumocistose (PJP), Neurotoxoplasmose e Criptococose"
    ],
    "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)": [
        "Dengue: classificação de risco e estadiamento clínico (Grupos A, B, C e D)",
        "Reconhecimento dos sinais de alarme e hidratação venosa imediata na Dengue grave",
        "Chikungunya (fase aguda e crônica articular) e Zika vírus",
        "Febre Amarela: formas graves, insuficiência hepatorrenal e vacinação",
        "Leptospirose (Síndrome de Weil) e Malária"
    ],
    "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias": [
        "Síndrome Nefrítica: GNPE, Nefropatia por IgA (Doença de Berger) e GNRP",
        "Síndrome Nefrótica: proteinúria nefrótica, hipoalbuminemia, edema e dislipidemia",
        "Glomerulopatias primárias: Lesão Mínima, GESF, Membranosa e Membranoproliferativa",
        "Glomerulopatias secundárias: Nefropatia Lúpica e Nefropatia Diabética",
        "Tubulopatias e Nefrite Intersticial Aguda (NIA)"
    ],
    "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base": [
        "Hiponatremia: classificação pela volemia e osmolaridade e prevenção da mielinólise pontina",
        "Hipernatremia: cálculo do déficit de água livre e correção gradual",
        "Distúrbios do Potássio: hipocalemia e hipercalemia (alterações no ECG e manejo de urgência)",
        "Gasometria arterial: acidose metabólica (ânion gap normal vs aumentado), alcalose metabólica e distúrbios respiratórios"
    ],
    "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)": [
        "Critérios diagnósticos e estadiamento da Injúria Renal Aguda (KDIGO)",
        "Diferenciação entre IRA pré-renal, intrínseca (NTA) e pós-renal (obstrutiva)",
        "Indicações de diálise de urgência na IRA",
        "Doença Renal Crônica: estadiamento pelo clearance de creatinina e proteinúria",
        "Manejo das complicações da DRC: anemia renal, distúrbio mineral e ósseo (hiperparatireoidismo secundário)"
    ],
    "Cefaleias Primárias (Enxaqueca, Tensional) e Secundárias de Alarme": [
        "Diagnóstico clínico das cefaleias primárias: Enxaqueca (Migrânea), Cefaleia Tensional e em Salvas",
        "Tratamento da crise aguda vs profilaxia medicamentosa da enxaqueca",
        "Sinais de alarme (Red Flags) para cefaleias secundárias e indicação de neuroimagem",
        "Arterite de células gigantes e Hemorragia Subaracnóidea (HSA)"
    ],
    "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares": [
        "Síndrome de Guillain-Barré: fisiopatologia desmielinizante, dissociação albuminocitológica e imunoglobulina",
        "Miastenia Gravis: autoanticorpos anti-AChR, crise miastênica e inibidores da acetilcolinesterase",
        "Esclerose Múltipla: manifestações clínicas disseminadas no tempo e espaço e tratamento modificador da doença",
        "Esclerose Lateral Amiotrófica (ELA) e neuropatias diabéticas periféricas"
    ],
    "Neurointensivismo, Morte Encefálica e Cuidados Críticos": [
        "Protocolo de determinação de Morte Encefálica segundo a Resolução CFM",
        "Manutenção do potencial doador de órgãos no ambiente de UTI",
        "Manejo do paciente com traumatismo e acidente vascular em terapia intensiva",
        "Sedação, analgesia e prevenção de Delirium no paciente crítico"
    ],
    "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)": [
        "Reconhecimento rápido do AVC agudo (Escala de Cincinnati e NIHSS)",
        "AVC Isquêmico: critérios de inclusão e exclusão para trombólise venosa com rtPA (até 4,5h)",
        "Indicações de trombectomia mecânica no AVC isquêmico agudo",
        "AVC Hemorrágico intraparenquimatoso: controle pressórico intensivo e indicações cirúrgicas",
        "Investigação etiológica (TOAST) e prevenção secundária do AVC"
    ],
    "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia": [
        "Avaliação laboratorial da coagulação: TAP/INR, TTPA e contagem de plaquetas",
        "Púrpura Trombocitopênica Imune (PTI) vs Púrpura Trombocitopênica Trombótica (PTT)",
        "Hemofilias A e B e Doença de von Willebrand",
        "Trombofilias hereditárias e Síndrome do Anticorpo Antifosfolípide (SAAF)",
        "Indicações de transfusão de hemocomponentes (concentrado de hemácias, plaquetas, plasma fresco e crioprecipitado)"
    ],
    "Leucemias, Linfomas e Mieloma Múltiplo": [
        "Leucemias Agudas (LLA e LMA): pancitopenia, blastos no sangue periférico e diagnóstico por mielograma",
        "Leucemias Crônicas (LMC e LLC): cromossomo Philadelphia e inibidores de tirosina quinase",
        "Linfoma de Hodgkin (células de Reed-Sternberg) vs Linfomas Não-Hodgkin: estadiamento de Ann Arbor",
        "Mieloma Múltiplo: critérios diagnósticos CRAB (Cálcio, Rim, Anemia e Lesões Ósseas)"
    ],
    "Diagnóstico Diferencial das Anemias e Hemoglobinopatias": [
        "Abordagem sistemática das anemias: volume corpuscular médio (VCM) e contagem de reticulócitos",
        "Anemia Ferropriva: perfil de ferro (ferritina baixa, transferrina alta) e reposição",
        "Anemia de Doença Crônica vs Anemias Megaloblásticas (deficiência de B12 e folato)",
        "Anemias Hemolíticas: coombs direto, esferocitose hereditária e deficiência de G6PD",
        "Doença Falciforme: crises vaso-oclusivas, sequestro esplênico, síndrome torácica aguda e hidroxiureia",
        "Talassemia Minor e Major: eletroforese de hemoglobina"
    ],
    "Tromboembolismo Pulmonar (TEP) e Hipertensão Pulmonar": [
        "Estratificação de probabilidade clínica de TEP: Escore de Wells e Escore de Geneva",
        "Papel do D-dímero e indicações de Angiotomografia de artérias pulmonares",
        "TEP de alto risco (instabilidade hemodinâmica): indicação de trombólise sistêmica",
        "Anticoagulação plena: heparinas vs novos anticoagulantes orais (DOACs)",
        "Hipertensão Pulmonar: classificação clínica dos 5 grupos e diagnóstico hemodinâmico"
    ],
    "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)": [
        "Diagnóstico espirométrico: distúrbio obstrutivo e resposta ao broncodilatador (VEF1/CVF < 0,70)",
        "Manejo da Asma crônica segundo o GINA: etapas de tratamento com corticoide inalatório + LABA",
        "Manejo da crise asmática aguda na sala de emergência",
        "DPOC: classificação GOLD (A, B, E), cessação do tabagismo e broncodilatadores de longa ação (LAMA/LABA)",
        "Exacerbação aguda da DPOC: indicações de antibióticos, corticoides sistêmicos e VNI"
    ],
    "Doenças Pulmonares Intersticiais e Fibrose Pulmonar": [
        "Padrões tomográficos de acometimento intersticial (Tomografia de Alta Resolução - TCAr)",
        "Fibrose Pulmonar Idiopática (FPI): padrão de Pneumonia Intersticial Usual (PIU) e antifibróticos",
        "Sarcoidose pulmonar: granulomas não caseosos, adenopatia hilar bilateral e manifestações extrapulmonares",
        "Pneumonite por Hipersensibilidade e acometimento pulmonar nas colagenoses"
    ],
    "Psiquiatria: Transtornos do Humor, Ansiedade e Psicoses": [
        "Transtorno Depressivo Maior: critérios do DSM-5 e farmacoterapia com antidepressivos (ISRS, IRSN)",
        "Transtorno Bipolar (Tipo I e II): diagnóstico de episódios maníacos/hipomaníacos e estabilizadores do humor (Lítio)",
        "Transtornos de ansiedade: Transtorno de Ansiedade Generalizada (TAG) e Transtorno do Pânico",
        "Esquizofrenia e transtornos psicóticos: sintomas positivos e negativos e antipsicóticos",
        "Avaliação do risco de suicídio e manejo de crises psiquiátricas"
    ],
    "Transtornos por Uso de Substâncias (Álcool, Tabaco e Drogas de Abuso)": [
        "Transtorno por uso de álcool: síndrome de abstinência alcoólica, Delirium Tremens e manejo com benzodiazepínicos",
        "Encefalopatia de Wernicke e Síndrome de Korsakoff: reposição profilática de tiamina (Vitamina B1)",
        "Cessação do tabagismo: terapia de reposição de nicotina, Bupropiona e Vareniclina",
        "Intoxicações agudas e abstinência por cocaína, opioides, canabinoides e anfetaminas"
    ],
    "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas": [
        "Artrite Reumatoide: poliartrite simétrica de pequenas articulações, Fator Reumatoide e Anti-CCP",
        "Tratamento da AR: DMARDs sintéticos (Metotrexato) e imunobiológicos",
        "Espondiloartrites: Espondilite Anquilosante, HLA-B27 e acometimento axial/sacroileíte",
        "Gota e artrites microcristalinas: hiperuricemia, cristais de urato monossódico e tratamento da crise vs profilaxia",
        "Diagnóstico diferencial com Artrite Infecciosa"
    ],
    "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias": [
        "Critérios diagnósticos do LES (EULAR/ACR): autoanticorpos (FAN, anti-DNA nativo, anti-Sm)",
        "Manejo do Lúpus e Nefrite Lúpica: Hidroxicloroquina, corticoides e imunossupressores",
        "Esclerose Sistêmica: forma cutânea limitada (CREST) vs difusa e crise renal esclerodérmica",
        "Miopatias inflamatórias: Dermatomiosite e Polimiosite (fraqueza proximal, enzimas musculares e biópsia)",
        "Síndrome de Sjögren e Síndrome Antifosfolípide"
    ],
    "Vasculites Sistêmicas dos Grandes, Médios e Pequenos Vasos": [
        "Vasculites de Grandes Vasos: Arterite de Takayasu e Arterite de Células Gigantes (Temporal)",
        "Vasculites de Médios Vasos: Poliarterite Nodosa (PAN) e Doença de Kawasaki",
        "Vasculites associadas ao ANCA (pequenos vasos): Granulomatose com Poliangiíte (Wegener) e Churg-Strauss",
        "Vasculites por imunocomplexos: Vasculite por IgA (Henoch-Schönlein) e Crioglobulinemia"
    ],
    "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica": [
        "Definições de Sepse e Choque Séptico segundo o consenso Sepsis-3 (Escore SOFA e qSOFA)",
        "Pacote da 1ª hora (Surviving Sepsis Campaign): lactato, hemoculturas e antibiótico de amplo espectro",
        "Ressuscitação volêmica com cristaloides (30 mL/kg) e metas hemodinâmicas",
        "Uso precoce de drogas vasoativas: Noradrenalina como vasopressor de 1ª escolha e Vasopressina",
        "Disfunções orgânicas e suporte em ambiente de terapia intensiva"
    ],
    "Ventilação Mecânica, SARA e Insuficiência Respiratória Aguda": [
        "Insuficiência respiratória aguda: Tipo 1 (hipoxêmica) vs Tipo 2 (hipercápnica)",
        "Indicações de intubação orotraqueal e sequência rápida de intubação (SRI)",
        "Princípios da Ventilação Mecânica: modos ventilatórios básicos (VCV, PCV e PSV)",
        "Síndrome do Desconforto Respiratório Agudo (SARA): critérios de Berlim e estratégia protetora (VT 6 mL/kg e PEEP)",
        "Manobra de prona e desmame ventilatório"
    ],
    "Toxicologia Clínica e Acidentes por Animais Peçonhentos": [
        "Toxidromes clássicas: anticolinérgica, colinérgica, opioide, simpaticomimética e sedativo-hipnótica",
        "Intoxicações por medicamentos comuns: Paracetamol (N-acetilcisteína), Benzodiazepínicos (Flumazenil) e Opioides (Naloxona)",
        "Intoxicação por organofosforados e carbamatos: atropinização e pralidoxima",
        "Acidentes por serpentes peçonhentas: gênero Bothrops (jararaca), Crotalus (cascavel), Lachesis (surucucu) e Micrurus (coral)",
        "Acidentes por escorpiões (Tityus serrulatus) e aranhas (Loxosceles e Phoneutria)"
    ]
}

# Update all taxonomy items
updated_count = 0
for area_data in tax:
    for macro in area_data.get("macroThemes", []):
        theme = macro["theme"]
        if theme in DETAILS_MAP:
            macro["details"] = DETAILS_MAP[theme]
            updated_count += 1

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(tax, f, ensure_ascii=False, indent=2)

print(f"Updated {updated_count} themes in taxonomy.json with rich 3-5 sub-topics!")
