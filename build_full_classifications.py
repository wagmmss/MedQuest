import json
import sys

# 1. Carregar taxonomia canônica
with open("canonical_taxonomy_170.json", "r", encoding="utf-8") as f:
    canon = json.load(f)

# 2. Carregar o dump original
with open("cm_b1.json", "r", encoding="utf-8") as f:
    batch = json.load(f)

# Mapeamento completo dos 100 itens com análise clínica especializada
classifications = [
    # 0: ID 72
    {
        "id": 72,
        "target_area": "Cirurgia",
        "target_subtema": "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)",
        "confidence": 1.0,
        "rationale": "Quadro de trombose venosa profunda (TVP) aguda de membro inferior em paciente oncológica pós-operatória de câncer de mama, cujo tratamento padrão é anticoagulação terapêutica com HBPM."
    },
    # 1: ID 79
    {
        "id": 79,
        "target_area": "Cirurgia",
        "target_subtema": "Aneurismas de Aorta Abdominal e Torácica",
        "confidence": 1.0,
        "rationale": "Emergência vascular aórtica (dissecção aguda de aorta torácica) com dor torácica lancinante, hipertensão severa e taquicardia, exigindo controle imediato da frequência cardíaca e duplo produto com esmolol IV."
    },
    # 2: ID 92
    {
        "id": 92,
        "target_area": "Cirurgia",
        "target_subtema": "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)",
        "confidence": 1.0,
        "rationale": "Trombose venosa profunda iliofemoral extensa em paciente com sangramento digestivo recente e cirurgia oncológica inadiável, configurando indicação clássica de filtro de veia cava inferior."
    },
    # 3: ID 192
    {
        "id": 192,
        "target_area": "Clínica Médica",
        "target_subtema": "Ventilação Mecânica, SARA e Insuficiência Respiratória Aguda",
        "confidence": 1.0,
        "rationale": "Manejo de insuficiência respiratória aguda e escolha de fármaco indutor hemodinamicamente estável (etomidato) para sequência rápida de intubação orotraqueal em paciente hipotenso/em choque."
    },
    # 4: ID 260
    {
        "id": 260,
        "target_area": "Clínica Médica",
        "target_subtema": "Valvopatias Adquiridas e Miocardiopatias",
        "confidence": 1.0,
        "rationale": "Diagnóstico de estenose aórtica grave de etiologia congênita (valva bicúspide) em paciente jovem com tríade clássica (angina, síncope e dispneia), pulso parvus et tardus e sopro ejetivo aórtico."
    },
    # 5: ID 261
    {
        "id": 261,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Desenvolvimento de Linfoma não-Hodgkin mediastinal complicando com síndrome da veia cava superior (SVCS) em paciente com história crônica de síndrome de Sjögren."
    },
    # 6: ID 262
    {
        "id": 262,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica de injúria renal aguda pós-renal / obstrutiva por hiperplasia prostática benigna em idoso com oligúria, sendo a ultrassonografia de vias urinárias o exame de escolha."
    },
    # 7: ID 263
    {
        "id": 263,
        "target_area": "Clínica Médica",
        "target_subtema": "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica",
        "confidence": 1.0,
        "rationale": "Otimização da terapia farmacológica com os quatro pilares modificadores de mortalidade na ICFEr (associação de betabloqueador e iSGLT2 em paciente já em uso de BRA e espironolactona)."
    },
    # 8: ID 264
    {
        "id": 264,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Diagnóstico diferencial de anemia normocítica e normocrômica com RDW normal em paciente com osteoartrite inflamatória e doença renal crônica leve, caracterizando anemia de doença crônica."
    },
    # 9: ID 265
    {
        "id": 265,
        "target_area": "Clínica Médica",
        "target_subtema": "Endocardite Infecciosa e Sepse de Foco Endovascular",
        "confidence": 1.0,
        "rationale": "Propêdêutica complementar em paciente com endocardite infecciosa com hemocultura negativa, exigindo sorologias para Bartonella spp., Coxiella burnetii e PCR para Tropheryma whipplei."
    },
    # 10: ID 266
    {
        "id": 266,
        "target_area": "Clínica Médica",
        "target_subtema": "Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo",
        "confidence": 1.0,
        "rationale": "Tratamento de infecção latente por tuberculose (ILTB) com isoniazida por 6 meses em paciente vivendo com HIV, assintomático, com CD4 > 350, RX de tórax normal e PPD reator."
    },
    # 11: ID 267
    {
        "id": 267,
        "target_area": "Clínica Médica",
        "target_subtema": "Infecções Sexualmente Transmissíveis (ISTs) no Adulto",
        "confidence": 1.0,
        "rationale": "Diagnóstico e tratamento de infecção gonocócica disseminada (artrite gonocócica com tenossinovite e lesões cutâneas pustulosas) causada por Neisseria gonorrhoeae, tratada com ceftriaxona e azitromicina."
    },
    # 12: ID 268
    {
        "id": 268,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Reconhecimento das indicações de diálise de urgência na doença renal crônica terminal agudizada, configurada pela uremia sintomática com encefalopatia e náuseas/vômitos refratários."
    },
    # 13: ID 269
    {
        "id": 269,
        "target_area": "Clínica Médica",
        "target_subtema": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
        "confidence": 1.0,
        "rationale": "Diagnóstico de peritonite bacteriana espontânea (PBE) em paciente cirrótico com ascite descompensada e contagem de polimorfonucleares no líquido ascítico >= 250/mm3."
    },
    # 14: ID 270
    {
        "id": 270,
        "target_area": "Clínica Médica",
        "target_subtema": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
        "confidence": 1.0,
        "rationale": "Manejo terapêutico inicial da encefalopatia hepática descompensada em paciente cirrótico com flapping (asterixis) e hálito hepático, mediante administração de lactulose oral/retal."
    },
    # 15: ID 271
    {
        "id": 271,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Ajuste de insulinoterapia no DM2 com hiperglicemia matinal de rebote decorrente de hipoglicemia noturna não percebida (efeito Somogyi), conduta: reduzir dose de NPH ao deitar."
    },
    # 16: ID 272
    {
        "id": 272,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Diagnóstico de hiperaldosteronismo primário em paciente jovem com hipertensão arterial resistente, fibrilação atrial e hipocalemia espontânea."
    },
    # 17: ID 273
    {
        "id": 273,
        "target_area": "Clínica Médica",
        "target_subtema": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
        "confidence": 1.0,
        "rationale": "Intervenção não farmacológica/nutricional de escolha para esteatose hepática associada à disfunção metabólica (MASLD) com fibrose: Dieta do Mediterrâneo associada à perda de peso."
    },
    # 18: ID 274
    {
        "id": 274,
        "target_area": "Clínica Médica",
        "target_subtema": "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)",
        "confidence": 1.0,
        "rationale": "Tratamento de via aérea única integrando asma brônquica e rinite crônica/medicamentosa, com corticoide inalatório e antileucotrieno e suspensão de vasoconstritor tópico nasal."
    },
    # 19: ID 275
    {
        "id": 275,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Conduta diante de exames diagnósticos discordantes e realização inadequada de TOTG (coleta em 1 hora em vez de 2 horas), sendo obrigatória a repetição correta do teste de tolerância à glicose oral."
    },
    # 20: ID 276
    {
        "id": 276,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Diagnóstico laboratorial de insuficiência adrenal secundária após desmame abrupto de corticoterapia crônica em paciente asmático, cursando classicamente com hiponatremia com potássio normal."
    },
    # 21: ID 277
    {
        "id": 277,
        "target_area": "Clínica Médica",
        "target_subtema": "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas",
        "confidence": 1.0,
        "rationale": "Manejo clínico de derrame pleural parapneumônico não complicado/simples (pH > 7,2, glicose > 60 mg/dL), indicando tratamento com antibiótico sistêmico (amoxicilina-clavulanato) sem necessidade de drenagem torácica."
    },
    # 22: ID 278
    {
        "id": 278,
        "target_area": "Clínica Médica",
        "target_subtema": "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)",
        "confidence": 1.0,
        "rationale": "Controle agudo de frequência cardíaca na fibrilação atrial estável em paciente portador de DPOC grave, sendo de escolha o bloqueador de canal de cálcio não diidropiridínico (diltiazem) para evitar broncoespasmo."
    },
    # 23: ID 279
    {
        "id": 279,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Tratamento de hipopituitarismo pan-hipofisário secundário a necrose hipofisária pós-parto (Síndrome de Sheehan), priorizando a reposição de glicocorticoide (prednisona) antes do hormônio tireoidiano."
    },
    # 24: ID 280
    {
        "id": 280,
        "target_area": "Clínica Médica",
        "target_subtema": "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos",
        "confidence": 1.0,
        "rationale": "Conduta conservadora em idoso muito idoso (>80 anos) com hipotireoidismo subclínico leve assintomático (TSH < 10 mUI/L e anti-TPO negativo): observação clínica periódica."
    },
    # 25: ID 281
    {
        "id": 281,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Investigação laboratorial inicial de causas secundárias de osteoporose e fratura por fragilidade em homem idoso, solicitando cálcio, fósforo e PTH."
    },
    # 26: ID 282
    {
        "id": 282,
        "target_area": "Clínica Médica",
        "target_subtema": "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da Doença de Graves (hipertireoidismo primário por autoanticorpos estimuladores do receptor de TSH - TRAb positivo) em mulher jovem com tireotoxicose e oftalmopatia."
    },
    # 27: ID 291
    {
        "id": 291,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Atendimento inicial à intoxicação aguda por defensivos agrícolas organofosforados/carbamatos com síndrome colinérgica, priorizando a descontaminação cutânea imediata e estabilização clínica."
    },
    # 28: ID 292
    {
        "id": 292,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)",
        "confidence": 1.0,
        "rationale": "Conduta na suspeita de síndrome coronariana aguda em unidade sem ECG disponível: administração imediata de AAS e transferência com urgência para emergência de referência."
    },
    # 29: ID 293
    {
        "id": 293,
        "target_area": "Clínica Médica",
        "target_subtema": "Dislipidemias, Síndrome Metabólica e Risco Cardiovascular",
        "confidence": 1.0,
        "rationale": "Estratificação de risco cardiovascular em paciente portadora de diabetes mellitus tipo 2 utilizando calculadora validada na Atenção Primária à Saúde."
    },
    # 30: ID 296
    {
        "id": 296,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Abordagem de suspeita de acidente elapídico vs ofídico não peçonhento: observação clínica na unidade de saúde, analgesia e descarte de soro antiofídico na ausência de manifestações neurotóxicas."
    },
    # 31: ID 297
    {
        "id": 297,
        "target_area": "Clínica Médica",
        "target_subtema": "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)",
        "confidence": 1.0,
        "rationale": "Fluxo da linha de cuidado no AVC isquêmico hiperagudo na rede de urgência: identificação precoce, regulação imediata e transporte prioritário para hospital com tomografia e trombólise."
    },
    # 32: ID 298
    {
        "id": 298,
        "target_area": "Clínica Médica",
        "target_subtema": "Hipertensão Arterial Sistêmica e Crises Hipertensivas",
        "confidence": 1.0,
        "rationale": "Confirmação diagnóstica de hipertensão arterial sistêmica em paciente com medidas de consultório limítrofes/estágio 1 através de MAPA ou MRPA segundo as diretrizes."
    },
    # 33: ID 302
    {
        "id": 302,
        "target_area": "Clínica Médica",
        "target_subtema": "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica",
        "confidence": 1.0,
        "rationale": "Tratamento de descompensação congestiva de insuficiência cardíaca (asma cardíaca com sibilância e linhas B no POCUS pulmonar) com diurético de alça (furosemida)."
    },
    # 34: ID 304
    {
        "id": 304,
        "target_area": "Clínica Médica",
        "target_subtema": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
        "confidence": 1.0,
        "rationale": "Profilaxia primária de sangramento por varizes esofágicas de grosso calibre em paciente com esquistossomose hepatoesplênica e hipertensão portal com betabloqueador não seletivo (carvedilol)."
    },
    # 35: ID 305
    {
        "id": 305,
        "target_area": "Clínica Médica",
        "target_subtema": "Valvopatias Adquiridas e Miocardiopatias",
        "confidence": 1.0,
        "rationale": "Diagnóstico etiológico de cardiomiopatia alcoólica dilatada com disfunção sistólica em paciente com consumo crônico e pesado de álcool e refluxo hepatojugular."
    },
    # 36: ID 306
    {
        "id": 306,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase",
        "confidence": 1.0,
        "rationale": "Manejo de prurido generalizado não alérgico induzido por opioides (tramadol), sendo a conduta correta a suspensão e substituição da medicação causadora."
    },
    # 37: ID 307
    {
        "id": 307,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)",
        "confidence": 1.0,
        "rationale": "Abordagem terapêutica imediata do infarto de ventrículo direito com hipotensão e campos pulmonares limpos, sendo a expansão volêmica com soro fisiológico a conduta prioritária."
    },
    # 38: ID 308
    {
        "id": 308,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Investigação propedêutica de pico monoclonal incidental sem critérios CRAB (gamopatia monoclonal de significado indeterminado) através de imunofixação e dosagem de cadeias leves livres."
    },
    # 39: ID 309
    {
        "id": 309,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Investigação de anemia microcítica e refratariedade à reposição de levotiroxina por má absorção em doença celíaca, com biópsia duodenal demonstrando infiltrado linfocítico intraepitelial."
    },
    # 40: ID 311
    {
        "id": 311,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Manejo de distúrbio hidroeletrolítico na cetoacidose diabética, priorizando a reposição de cloreto de potássio antes de iniciar a infusão contínua de insulina quando há hipocalemia ou fraqueza muscular."
    },
    # 41: ID 313
    {
        "id": 313,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica de Linfoma de Hodgkin em paciente com adenopatia cervical endurecida e indolor associada a sintomas B e prurido refratário, com biópsia excisional do linfonodo."
    },
    # 42: ID 314
    {
        "id": 314,
        "target_area": "Clínica Médica",
        "target_subtema": "Hipertensão Arterial Sistêmica e Crises Hipertensivas",
        "confidence": 1.0,
        "rationale": "Técnica correta de aferição da pressão arterial em consultório, exigindo a adequação do comprimento e da largura do manguito à circunferência do braço do paciente obeso."
    },
    # 43: ID 316
    {
        "id": 316,
        "target_area": "Clínica Médica",
        "target_subtema": "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas",
        "confidence": 1.0,
        "rationale": "Tratamento de pneumonia nosocomial/hospitalar em paciente internado com tosse produtiva e febre, utilizando piperacilina com tazobactam e desconsiderando S. epidermidis isolado em um único frasco de hemocultura."
    },
    # 44: ID 317
    {
        "id": 317,
        "target_area": "Clínica Médica",
        "target_subtema": "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares",
        "confidence": 1.0,
        "rationale": "Reconhecimento de parkinsonismo secundário medicamentoso induzido pelo uso de antieméticos antagonistas dopaminérgicos centrais (bromoprida) em paciente hospitalizado."
    },
    # 45: ID 318
    {
        "id": 318,
        "target_area": "Clínica Médica",
        "target_subtema": "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias",
        "confidence": 1.0,
        "rationale": "Manejo de atividade de lúpus eritematoso sistêmico com nefrite lúpica, disfunção renal aguda e hipercalemia com sobrecarga hídrica, tratada de imediato com diurético de alça (furosemida)."
    },
    # 46: ID 319
    {
        "id": 319,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Avaliação de hipertensão arterial grave em paciente em diálise crônica através da pesagem corporal e estimativa do ganho de peso interdialítico e peso seco."
    },
    # 47: ID 320
    {
        "id": 320,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Diagnóstico clínico de emergência oncológica metabólica (hipercalcemia da malignidade) em paciente com câncer de mama e metástases ósseas apresentando rebaixamento do nível de consciência e constipação."
    },
    # 48: ID 321
    {
        "id": 321,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio",
        "confidence": 1.0,
        "rationale": "Manejo de estresse agudo infeccioso em paciente com insuficiência adrenal crônica (regras de dias de doença / sick day rules), dobrando/aumentando a dose de hidrocortisona para prevenir crise addisoniana."
    },
    # 49: ID 339
    {
        "id": 339,
        "target_area": "Cirurgia",
        "target_subtema": "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos",
        "confidence": 1.0,
        "rationale": "Seguimento pós-operatório de carcinoma medular de tireoide (neoplasia das células parafoliculares/C) após tireoidectomia total através da dosagem periódica de calcitonina sérica."
    },
    # 50: ID 341
    {
        "id": 341,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Indicação de inibidor de SGLT2 (dapagliflozina) em paciente com diabetes mellitus tipo 2 descompensado associado a doença renal crônica leve/moderada pela nefroproteção e controle glicêmico."
    },
    # 51: ID 344
    {
        "id": 344,
        "target_area": "Clínica Médica",
        "target_subtema": "Infecções Sexualmente Transmissíveis (ISTs) no Adulto",
        "confidence": 1.0,
        "rationale": "Tratamento de sífilis latente tardia ou de duração indeterminada em paciente assintomático com testes treponêmico e não treponêmico reagentes com penicilina benzatina 2,4 milhões UI semanal por 3 semanas."
    },
    # 52: ID 346
    {
        "id": 346,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Diagnóstico de acidente loxoscélico (picada de aranha-marrom Loxosceles spp.) com placa marmórea e necrose cutânea progressiva após manuseio de entulhos de construção."
    },
    # 53: ID 349
    {
        "id": 349,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatoses Infecciosas, Hanseníase e Leishmanioses",
        "confidence": 1.0,
        "rationale": "Diagnóstico de eritema nodoso hansênico (reação hansênica tipo 2) com nódulos dolorosos, febre alta e alteração de sensibilidade periférica em área endêmica."
    },
    # 54: ID 350
    {
        "id": 350,
        "target_area": "Clínica Médica",
        "target_subtema": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
        "confidence": 1.0,
        "rationale": "Tratamento imediato de hipercalemia grave com alterações eletrocardiográficas e acidose metabólica grave, com gluconato de cálcio a 10% EV para estabilização de membrana miocárdica."
    },
    # 55: ID 351
    {
        "id": 351,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica de Leucemia Mieloide Crônica (LMC) em paciente com esplenomegalia maciça, desvio escalonado à esquerda, basofilia e trombocitose, solicitando pesquisa de BCR::ABL1."
    },
    # 56: ID 352
    {
        "id": 352,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase",
        "confidence": 1.0,
        "rationale": "Investigação de dermatite de contato alérgica facial eczematosa com exacerbação a cosméticos e fragrâncias através do teste de contato (Patch Test)."
    },
    # 57: ID 353
    {
        "id": 353,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatoses Infecciosas, Hanseníase e Leishmanioses",
        "confidence": 1.0,
        "rationale": "Diagnóstico laboratorial de candidíase intertriginosa em paciente diabética com intertrigo inguinal agravado por corticosteroide tópico: visualização de pseudohifas ao exame micológico direto com KOH."
    },
    # 58: ID 354
    {
        "id": 354,
        "target_area": "Clínica Médica",
        "target_subtema": "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos",
        "confidence": 1.0,
        "rationale": "Controle de resposta ventricular em fibrilação atrial precipitada por tireotoxicose com propranolol oral, que adicionalmente bloqueia a conversão periférica de T4 em T3."
    },
    # 59: ID 355
    {
        "id": 355,
        "target_area": "Clínica Médica",
        "target_subtema": "Valvopatias Adquiridas e Miocardiopatias",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da insuficiência aórtica crônica com sopro aspirativo holodiastólico na borda esternal esquerda e ictus desviado, cursando com sobrecarga volumétrica e hipertrofia excêntrica do VE."
    },
    # 60: ID 356
    {
        "id": 356,
        "target_area": "Cirurgia",
        "target_subtema": "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos",
        "confidence": 1.0,
        "rationale": "Diagnóstico de pancreatite crônica com insuficiência exócrina e esteatorreia em paciente etilista crônico de longa data com dor epigástrica pós-prandial em faixa e perda ponderal."
    },
    # 61: ID 357
    {
        "id": 357,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Manejo de diabetes mellitus tipo 2 com descompensação grave e sintomas catabólicos (HbA1c 10,8% e emagrecimento), indicando suspensão da sulfonilureia e início de insulinoterapia basal-bolus (NPH e regular)."
    },
    # 62: ID 358
    {
        "id": 358,
        "target_area": "Clínica Médica",
        "target_subtema": "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica",
        "confidence": 1.0,
        "rationale": "Semiologia cardiovascular na insuficiência cardíaca descompensada com fração de ejeção reduzida: refluxo hepatojugular como sinal fidedigno de sobrecarga pressórica no ventrículo direito."
    },
    # 63: ID 359
    {
        "id": 359,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Abordagem da cistite aguda não complicada em mulher jovem sem fatores de risco: tratamento empírico de primeira linha com nitrofurantoína por 5 dias sem necessidade de exames complementares."
    },
    # 64: ID 360
    {
        "id": 360,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatoses Infecciosas, Hanseníase e Leishmanioses",
        "confidence": 1.0,
        "rationale": "Diagnóstico e tratamento com itraconazol da paracoccidioidomicose forma crônica em lavrador de café com lesões orais em estomatite moriforme e infiltrado pulmonar."
    },
    # 65: ID 361
    {
        "id": 361,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Manejo de portador de traço falciforme (heterozigose HbAS assintomático com HbS 38% e hemograma normal), cuja conduta clínica recomendada é o aconselhamento genético."
    },
    # 66: ID 362
    {
        "id": 362,
        "target_area": "Clínica Médica",
        "target_subtema": "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática",
        "confidence": 1.0,
        "rationale": "Investigação de alteração neurológica aguda com déficit focal (hemiparesia) em paciente cirrótica, indicando TC de crânio urgente para afastar AVC ou lesão estrutural antes de atribuir à encefalopatia hepática."
    },
    # 67: ID 363
    {
        "id": 363,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da anemia de doença crônica em artrite reumatoide de alta atividade inflamatória, cursando classicamente com contagem de reticulócitos reduzida por hipoproliferação medular."
    },
    # 68: ID 364
    {
        "id": 364,
        "target_area": "Clínica Médica",
        "target_subtema": "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)",
        "confidence": 1.0,
        "rationale": "Manejo de gestante com asma brônquica bem controlada em uso de corticoide inalatório e LABA (budesonida + formoterol), recomendando a manutenção rigorosa do esquema profilático."
    },
    # 69: ID 365
    {
        "id": 365,
        "target_area": "Clínica Médica",
        "target_subtema": "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas",
        "confidence": 1.0,
        "rationale": "Etiologia de complicação bacteriana secundária pós-síndrome gripal (pneumonia pós-influenza com padrão bifásico e gravidade), causada tipicamente por Staphylococcus aureus."
    },
    # 70: ID 366
    {
        "id": 366,
        "target_area": "Clínica Médica",
        "target_subtema": "Doenças Pulmonares Intersticiais e Fibrose Pulmonar",
        "confidence": 1.0,
        "rationale": "Semiologia do distúrbio restritivo pulmonar em pneumoconiose / doença pulmonar intersticial crônica avançada com baqueteamento digital: redução da expansibilidade torácica."
    },
    # 71: ID 367
    {
        "id": 367,
        "target_area": "Clínica Médica",
        "target_subtema": "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas",
        "confidence": 1.0,
        "rationale": "Diagnóstico clínico e radiológico de osteoartrite das mãos em trabalhador braçal com nódulos ósseos interfalangeanos (Heberden e Bouchard) e dor de ritmo puramente mecânico."
    },
    # 72: ID 368
    {
        "id": 368,
        "target_area": "Clínica Médica",
        "target_subtema": "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica",
        "confidence": 1.0,
        "rationale": "Emergência onco-hematológica: neutropenia febril (neutrófilos < 500/mm3 e febre >= 38°C) em pós-quimioterapia, exigindo início imediato de antibioticoterapia antipseudomonas empírica com cefepime IV."
    },
    # 73: ID 369
    {
        "id": 369,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Diagnóstico de ateroembolismo de colesterol (síndrome dos cristais de colesterol) com livedo reticular, eosinofilia e hipocomplementemia após procedimento vascular invasivo (angioplastia coronariana)."
    },
    # 74: ID 370
    {
        "id": 370,
        "target_area": "Cirurgia",
        "target_subtema": "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica de tumor do sulco superior (tumor de Pancoast) em paciente tabagista com síndrome de Horner (ptose e miose) e plexopatia braquial, diagnosticado por TC de tórax."
    },
    # 75: ID 371
    {
        "id": 371,
        "target_area": "Clínica Médica",
        "target_subtema": "Hepatites Virais (A, B, C) e Icterícias Metabólicas",
        "confidence": 1.0,
        "rationale": "Interpretação sorológica do perfil de infecção resolvida/curada pelo vírus da hepatite B (HBsAg negativo, anti-HBc total positivo e anti-HBs positivo)."
    },
    # 76: ID 372
    {
        "id": 372,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Investigação etiológica mandatória de anemia ferropriva microcítica e hipocrômica em homem adulto, necessitando de endoscopia digestiva alta e colonoscopia para descartar neoplasias do TGI."
    },
    # 77: ID 373
    {
        "id": 373,
        "target_area": "Clínica Médica",
        "target_subtema": "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica",
        "confidence": 1.0,
        "rationale": "Tratamento de descompensação volêmica de insuficiência cardíaca com derrame pleural transudativo e ortopneia mediante otimização da dose de diurético de alça."
    },
    # 78: ID 374
    {
        "id": 374,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Reconhecimento de mieloma múltiplo complicado por hipercalcemia sintomática manifestando-se com delirium/confusão mental aguda, lesão lítica em coluna e disfunção renal, indicando dosagem de cálcio sérico."
    },
    # 79: ID 375
    {
        "id": 375,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Diagnóstico laboratorial diferencial de anemia ferropriva clássica com queilite angular, VCM baixo, ferritina baixa (<15 ng/mL) e aumento da capacidade total de ligação do ferro (TIBC elevado)."
    },
    # 80: ID 376
    {
        "id": 376,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Diagnóstico de Púrpura Trombocitopênica Trombótica (PTT) caracterizada por anemia hemolítica microangiopática com esquizócitos no sangue periférico, plaquetopenia de consumo e sintomas neurológicos flutuantes."
    },
    # 81: ID 377
    {
        "id": 377,
        "target_area": "Cirurgia",
        "target_subtema": "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica do divertículo faringoesofágico de Zenker em idoso com regurgitação de alimentos não digeridos, halitose e broncoaspiração, sendo a videofluoroscopia/esofagograma baritado o exame inicial de escolha."
    },
    # 82: ID 378
    {
        "id": 378,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Fisiopatologia do distúrbio mineral e ósseo na DRC estágio 4 avançada (hiperparatireoidismo secundário por retenção de fosfato e hipocalcemia, levando ao aumento do PTH sérico)."
    },
    # 83: ID 380
    {
        "id": 380,
        "target_area": "Clínica Médica",
        "target_subtema": "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas",
        "confidence": 1.0,
        "rationale": "Diagnóstico de artrite gotosa aguda (crise de gota) por artrocentese demonstrando líquido sinovial inflamatório com cristais de urato monossódico em forma de agulha com birrefringência fortemente negativa."
    },
    # 84: ID 381
    {
        "id": 381,
        "target_area": "Clínica Médica",
        "target_subtema": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da hipocalemia induzida por fármacos broncodilatadores: aumento da atividade beta-2-adrenérgica estimulando o influxo celular de potássio via bomba Na+/K+-ATPase."
    },
    # 85: ID 382
    {
        "id": 382,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Manejo de edema periférico em membros inferiores secundário a efeito adverso de gabapentinoide (pregabalina), com melhora após a suspensão da medicação."
    },
    # 86: ID 394
    {
        "id": 394,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Torácica Geral e Doenças Pleurais",
        "confidence": 1.0,
        "rationale": "Primeiro passo propedêutico e terapêutico mandatório na abordagem de derrame pleural volumoso sintomático evidenciado em radiografia de tórax: toracocentese diagnóstica e de alívio."
    },
    # 87: ID 395
    {
        "id": 395,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Tratamento da cardiotoxicidade por intoxicação sistêmica por anestésicos locais (LAST) após infiltrações múltiplas com taquicardia ventricular e bloqueio de canais de sódio com bicarbonato de sódio."
    },
    # 88: ID 396
    {
        "id": 396,
        "target_area": "Clínica Médica",
        "target_subtema": "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)",
        "confidence": 1.0,
        "rationale": "Topografia vascular e lesional no AVC isquêmico lacunar: síndrome motora pura hemifacial e hemiparesia braquiocrural por infarto lacunar na cápsula interna (braço posterior)."
    },
    # 89: ID 397
    {
        "id": 397,
        "target_area": "Clínica Médica",
        "target_subtema": "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)",
        "confidence": 1.0,
        "rationale": "Diagnóstico e manejo de nefrite intersticial aguda (NIA) alérgica induzida por antibiótico beta-lactâmico (cefalexina) com eosinofilúria e hematúria, tratando com a interrupção imediata da droga."
    },
    # 90: ID 399
    {
        "id": 390,  # Note: verify if ID 399
        "id": 399,
        "target_area": "Clínica Médica",
        "target_subtema": "Infecções Sexualmente Transmissíveis (ISTs) no Adulto",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da Reação de Jarisch-Herxheimer após tratamento inicial de neurossífilis/sífilis terciária: liberação maciça de endotoxinas/lipoproteínas e citocinas inflamatórias após a lise bacteriana."
    },
    # 91: ID 405
    {
        "id": 405,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Anamnese dirigida na investigação de anemia ferropriva por sangramento oculto em mulher pré-menopáusica com laqueadura, sendo prioritária a avaliação detalhada do padrão de fluxo menstrual."
    },
    # 92: ID 407
    {
        "id": 407,
        "target_area": "Clínica Médica",
        "target_subtema": "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)",
        "confidence": 1.0,
        "rationale": "Manejo da asma leve controlada segundo diretrizes da GINA (Etapa 1 e 2): uso de corticoide inalatório em baixa dose associado a beta-2 agonista de longa duração (formoterol) sob demanda/alívio."
    },
    # 93: ID 408
    {
        "id": 408,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase",
        "confidence": 1.0,
        "rationale": "Diagnóstico dermatológico de onicólise ungueal mecânica/traumática caracterizada pelo descolamento indolor da lâmina ungueal do leito ('unha oca')."
    },
    # 94: ID 411
    {
        "id": 411,
        "target_area": "Clínica Médica",
        "target_subtema": "Endocardite Infecciosa e Sepse de Foco Endovascular",
        "confidence": 1.0,
        "rationale": "Diagnóstico ecocardiográfico de endocardite infecciosa em valva aórtica bicúspide identificando imagem de vegetação valvar ecogênica móvel e regurgitação valvar."
    },
    # 95: ID 412
    {
        "id": 412,
        "target_area": "Clínica Médica",
        "target_subtema": "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)",
        "confidence": 1.0,
        "rationale": "Conduta na taquiarritmia instável com sinais de congestão pulmonar aguda (edema agudo de pulmão com estertores crepitantes bilaterais e taquicardia extrema): cardioversão elétrica sincronizada imediata."
    },
    # 96: ID 413
    {
        "id": 413,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase",
        "confidence": 1.0,
        "rationale": "Diagnóstico de pênfigo foliáceo (doença bolhosa autoimune superficial por anticorpos anti-desmogleína 1) com bolhas flácidas em áreas seborreicas, sem acometimento de mucosas e sinal de Nikolsky positivo."
    },
    # 97: ID 414
    {
        "id": 414,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Ressuscitação clínica prioritária na cetoacidose diabética (CAD) com hipotensão e desidratação grave: administração intravenosa imediata de solução isotônica de cloreto de sódio 0,9%."
    },
    # 98: ID 415
    {
        "id": 415,
        "target_area": "Clínica Médica",
        "target_subtema": "Hepatites Virais (A, B, C) e Icterícias Metabólicas",
        "confidence": 1.0,
        "rationale": "Confirmação diagnóstica de hepatite C ativa e viremia em paciente assintomático com anti-HCV reagente através da solicitação de teste molecular quantitativo de RNA-HCV."
    },
    # 99: ID 416
    {
        "id": 416,
        "target_area": "Cirurgia",
        "target_subtema": "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos",
        "confidence": 1.0,
        "rationale": "Distúrbio nutricional da má absorção lipídica por insuficiência pancreática exócrina em pancreatite crônica alcoólica: deficiência de vitaminas lipossolúveis (Vitamina A)."
    }
]

# Validação estrita contra os 170 temas canônicos
errors = []
if len(classifications) != len(batch):
    errors.append(f"Tamanho inconsistente: batch tem {len(batch)} e classificações tem {len(classifications)}")

batch_ids = {q["id"] for q in batch}
classified_ids = {c["id"] for c in classifications}

if batch_ids != classified_ids:
    errors.append(f"IDs divergentes! Diferença: {batch_ids ^ classified_ids}")

for item in classifications:
    area = item["target_area"]
    sub = item["target_subtema"]
    if area not in canon:
        errors.append(f"ID {item['id']}: Área '{area}' não existe na taxonomia canônica.")
    elif sub not in canon[area]:
        errors.append(f"ID {item['id']}: Subtema '{sub}' não pertence à área '{area}' na taxonomia canônica.")

if errors:
    print("ERROS DE VALIDAÇÃO:")
    for e in errors:
        print("-", e)
    sys.exit(1)
else:
    print(f"Sucesso total: Todas as {len(classifications)} questões validadas com 100% de conformidade canônica!")
    
    # Salvar em cm_b1_classified.json
    output_path = "cm_b1_classified.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(classifications, f, ensure_ascii=False, indent=2)
    print(f"Arquivo '{output_path}' gerado com sucesso!")
