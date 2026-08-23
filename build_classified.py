import json

# Carregar taxonomia
with open("canonical_taxonomy_170.json", "r", encoding="utf-8") as f:
    TAX_170 = json.load(f)

ALL_THEMES = {}
for area, themes in TAX_170.items():
    for t in themes:
        ALL_THEMES[t] = area

# Mapeamento completo e fundamentado dos 100 itens de ped_b1.json
# Cada entrada contém: id, target_area, target_subtema, confidence (1.0), rationale clínica detalhada.

classifications = [
    # 0: ID 21
    {
        "id": 21,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente submetido à esofagocoloplastia por atresia de esôfago que evolui com necrose isquêmica do enxerto colônico transposto. Trata-se de complicação cirúrgica maior no contexto de malformações digestivas neonatais e cirurgia pediátrica."
    },
    # 1: ID 90
    {
        "id": 90,
        "target_area": "Cirurgia",
        "target_subtema": "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo",
        "confidence": 1.0,
        "rationale": "Criança pré-escolar com massa palpável em flanco esquerdo, hematúria e imagem compatível com Tumor de Wilms (nefroblastoma), a neoplasia renal maligna mais frequente da infância, classificada em uro-oncologia renal."
    },
    # 2: ID 94
    {
        "id": 94,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente de 4 meses com atresia de vias biliares diagnosticada tardiamente com cirrose descompensada e ascite, tendo indicação de transplante hepático devido à perda da janela para cirurgia de Kasai."
    },
    # 3: ID 95
    {
        "id": 95,
        "target_area": "Pediatria",
        "target_subtema": "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento",
        "confidence": 1.0,
        "rationale": "Lactente de 2 meses com testículo não palpável unilateralmente (criptorquidia). A conduta em puericultura é expectante até os 6 meses aguardando o pico de testosterona da minipuberdade."
    },
    # 4: ID 96
    {
        "id": 96,
        "target_area": "Cirurgia",
        "target_subtema": "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)",
        "confidence": 1.0,
        "rationale": "Lactente com hérnia inguinal encarcerada complicada por sofrimento de alça e obstrução intestinal, com indicação cirúrgica emergencial mandatória."
    },
    # 5: ID 111
    {
        "id": 111,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Recém-nascido com associação VACTERL (atresia de esôfago sem fístula distal, atresia anal e malformações de membros), demandando ultrassonografia de rins e vias urinárias para rastreio de anomalias urológicas associadas."
    },
    # 6: ID 112
    {
        "id": 112,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Quadro clássico de atresia de esôfago com sialorreia profusa, engasgo e cianose na primeira mamada em RN com antecedente de polidrâmnio, confirmado pela passagem de sonda orogástrica e radiografia."
    },
    # 7: ID 130
    {
        "id": 130,
        "target_area": "Pediatria",
        "target_subtema": "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil",
        "confidence": 1.0,
        "rationale": "Lactente jovem com regurgitações pós-mamadas de leite materno sem repercussão ponderal ou sinais de alarme, compatível com refluxo gastroesofágico fisiológico do lactente ('regurgitador feliz')."
    },
    # 8: ID 141
    {
        "id": 141,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente com intussuscepção intestinal aguda ('fezes em geleia de framboesa', cólicas e letargia), cuja conduta diagnóstica e terapêutica imediata na ausência de peritonite é o enema opaco."
    },
    # 9: ID 151
    {
        "id": 151,
        "target_area": "Cirurgia",
        "target_subtema": "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino",
        "confidence": 1.0,
        "rationale": "Achado radiológico de cisto broncogênico no mediastino médio em criança, clássica lesão congênita cística mediastinal."
    },
    # 10: ID 158
    {
        "id": 158,
        "target_area": "Cirurgia",
        "target_subtema": "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica",
        "confidence": 1.0,
        "rationale": "Hemorragia digestiva alta varicosa (melena) por hipertensão portal pós-portoenterostomia (cirurgia de Kasai), exigindo estabilização e infusão imediata de vasoconstritor esplâncnico."
    },
    # 11: ID 166
    {
        "id": 166,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente com quadro típico de intussuscepção intestinal encaminhado para enema opaco, cujo resultado esperado é a redução hidrostática do intussuscepto."
    },
    # 12: ID 175
    {
        "id": 175,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente de 6 meses com atresia de vias biliares em fase cirrótica avançada (INR alargado, hipoalbuminemia), sendo o transplante hepático a única abordagem curativa indicada."
    },
    # 13: ID 176
    {
        "id": 176,
        "target_area": "Cirurgia",
        "target_subtema": "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas",
        "confidence": 1.0,
        "rationale": "Mau posicionamento de sonda nasogástrica na árvore traqueobrônquica identificada na radiografia de controle pós-passagem, demandando retirada imediata da sonda para prevenir broncoaspiração e pneumotórax."
    },
    # 14: ID 177
    {
        "id": 177,
        "target_area": "Cirurgia",
        "target_subtema": "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)",
        "confidence": 1.0,
        "rationale": "Criança com quadro de íleo paralítico funcional desencadeado por hipocalemia (K+ 2,9 mEq/L) secundária a gastroenterite aguda, cursando com distensão abdominal e redução dos RHA."
    },
    # 15: ID 193
    {
        "id": 193,
        "target_area": "Cirurgia",
        "target_subtema": "Fundamentos da Anestesiologia, Farmacologia e Bloqueios",
        "confidence": 1.0,
        "rationale": "Sedoanalgesia para redução incruenta de luxação articular em criança asmática; a cetamina é o fármaco de escolha devido ao seu efeito broncodilatador e manutenção dos reflexos protetores de via aérea."
    },
    # 16: ID 194
    {
        "id": 194,
        "target_area": "Cirurgia",
        "target_subtema": "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo",
        "confidence": 1.0,
        "rationale": "Quadro clínico típico de Tumor de Wilms (nefroblastoma) em criança menor de 3 anos, apresentando massa abdominal firme e indolor no flanco que não cruza a linha média."
    },
    # 17: ID 200
    {
        "id": 200,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente de 45 dias com vômitos pós-prandiais não biliosos em jato e perda ponderal, quadro patognomônico de estenose hipertrófica do piloro."
    },
    # 18: ID 205
    {
        "id": 205,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente de 6 meses com intussuscepção intestinal (dor em cólica, sinal de Dance, fezes em geleia de morango), cuja melhor conduta inicial é o enema opaco terapêutico."
    },
    # 19: ID 206
    {
        "id": 206,
        "target_area": "Cirurgia",
        "target_subtema": "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco",
        "confidence": 1.0,
        "rationale": "Paciente jovem pós-trauma torácico apresentando hemotórax retido/coagulado e febre, com indicação padrão de videotoracoscopia (VATS) para evacuação e decorticação precoce."
    },
    # 20: ID 207
    {
        "id": 207,
        "target_area": "Cirurgia",
        "target_subtema": "Atendimento ao Paciente Queimado e Reposição Volêmica",
        "confidence": 1.0,
        "rationale": "Vítima de queimadura em ambiente fechado com queimaduras faciais e sinais de lesão inalatória, cuja conduta prioritária imediata no protocolo do queimado é a intubação orotraqueal e oxigênio a 100%."
    },
    # 21: ID 208
    {
        "id": 208,
        "target_area": "Cirurgia",
        "target_subtema": "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas",
        "confidence": 1.0,
        "rationale": "Isquemia crítica crônica de membro inferior por DAOP (dor em repouso e cianose fixa de hálux), demandando arteriografia para planejamento terapêutico de revascularização arterial."
    },
    # 22: ID 209
    {
        "id": 209,
        "target_area": "Cirurgia",
        "target_subtema": "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)",
        "confidence": 1.0,
        "rationale": "Insuficiência venosa crônica avançada (CEAP 6) com úlcera venosa maleolar, dermite ocre e varizes tronculares; manejo com elastocompressão, perda ponderal e cirurgia de varizes."
    },
    # 23: ID 210
    {
        "id": 210,
        "target_area": "Cirurgia",
        "target_subtema": "Trauma Raquimedular (TRM) e Lesões Vertebrais",
        "confidence": 1.0,
        "rationale": "Paciente com TRM cervical após agressão desenvolvendo insuficiência respiratória aguda por perda de inervação diafragmática/intercostal, com indicação de intubação com imobilização cervical em linha."
    },
    # 24: ID 211
    {
        "id": 211,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Lactente com Doença de Hirschsprung complicada por enterocolite aguda associada; a conduta de urgência mandatória é a descompressão colorretal imediata com lavagens intestinais."
    },
    # 25: ID 212
    {
        "id": 212,
        "target_area": "Cirurgia",
        "target_subtema": "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)",
        "confidence": 1.0,
        "rationale": "Tromboprofilaxia farmacológica estendida (4 a 6 semanas) com HBPM ou DOACs no pós-operatório de artroplastia total de quadril, cirurgia ortopédica de altíssimo risco para TEV."
    },
    # 26: ID 213
    {
        "id": 213,
        "target_area": "Cirurgia",
        "target_subtema": "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas",
        "confidence": 1.0,
        "rationale": "Saída abundante de secreção serossanguinolenta em 'água de carne' pela incisão cirúrgica no 7º DPO de laparotomia, definindo deiscência aponeurótica da ferida operatória."
    },
    # 27: ID 214
    {
        "id": 214,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Recém-nascido com cloaca persistente (anomalia anorretal complexa com orifício perineal único) apresentando massa abdominal palpável decorrente de hidronefrose obstrutiva urogenital."
    },
    # 28: ID 215
    {
        "id": 215,
        "target_area": "Cirurgia",
        "target_subtema": "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas",
        "confidence": 1.0,
        "rationale": "Sangramento vivo em grande volume pela cânula de traqueostomia após 4 semanas de ventilação mecânica, patognomônico de fístula tráqueo-inominada (erosão da artéria inominada)."
    },
    # 29: ID 216
    {
        "id": 216,
        "target_area": "Cirurgia",
        "target_subtema": "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico",
        "confidence": 1.0,
        "rationale": "Priorização de procedimentos cirúrgicos eletivos/urgentes em cenários de restrição de recursos hospitalares (reconstrução de trânsito intestinal para viabilizar desospitalização de paciente em NPT)."
    },
    # 30: ID 217
    {
        "id": 217,
        "target_area": "Cirurgia",
        "target_subtema": "Litíase Biliar, Colecistite, Coledocolitíase e Colangite",
        "confidence": 1.0,
        "rationale": "Quadro clínico de colecistite aguda litiásica leve (Grau I de Tóquio), com indicação cirúrgica padrão-ouro de colecistectomia videolaparoscópica precoce."
    },
    # 31: ID 218
    {
        "id": 218,
        "target_area": "Cirurgia",
        "target_subtema": "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas",
        "confidence": 1.0,
        "rationale": "Protocolo e critérios de segurança para decanulação de traqueostomia em paciente crítico recuperado de insuficiência respiratória (tolerância à oclusão por 24 horas)."
    },
    # 32: ID 240
    {
        "id": 240,
        "target_area": "Cirurgia",
        "target_subtema": "Cirurgia Pediátrica e Malformações Digestivas Neonatais",
        "confidence": 1.0,
        "rationale": "Doença de Hirschsprung (megacólon aganglionar congênito) em pré-escolar apresentando episódios recorrentes de falsa 'diarreia' causados por enterocolite associada."
    },
    # 33: ID 299
    {
        "id": 299,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Tríade clássica de Síndrome Hemolítico-Urêmica (SHU) pós-diarreica: anemia hemolítica microangiopática com esquizócitos, trombocitopenia e insuficiência renal aguda oligoanúrica."
    },
    # 34: ID 300
    {
        "id": 300,
        "target_area": "Pediatria",
        "target_subtema": "Alojamento Conjunto e Testes de Triagem Neonatal (Pezinho, Olhinho, Coraçãozinho)",
        "confidence": 1.0,
        "rationale": "Fluxograma de triagem neonatal para fibrose cística: duas dosagens consecutivas de IRT elevadas no teste do pezinho exigem confirmação diagnóstica pelo teste do suor com dosagem de cloro."
    },
    # 35: ID 301
    {
        "id": 301,
        "target_area": "Clínica Médica",
        "target_subtema": "Meningites, Encefalites e Infecções do SNC",
        "confidence": 1.0,
        "rationale": "Meningite viral asséptica em adolescente, caracterizada por pleocitose moderada com predomínio linfomononuclear, glicorraquia normal e discreta elevação de proteínas no líquor."
    },
    # 36: ID 303
    {
        "id": 303,
        "target_area": "Clínica Médica",
        "target_subtema": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da hiponatremia hipovolêmica secundária a diarreia aguda: a depleção de volume ativa o sistema renina-angiotensina-aldosterona e a secreção de ADH para retenção hidrossalina."
    },
    # 37: ID 329
    {
        "id": 329,
        "target_area": "Pediatria",
        "target_subtema": "Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica",
        "confidence": 1.0,
        "rationale": "Manejo da bacteriemia relacionada a cateter por Staphylococcus aureus em paciente pediátrico dialítico, exigindo remoção do cateter e manutenção de vancomicina parenteral."
    },
    # 38: ID 330
    {
        "id": 330,
        "target_area": "Pediatria",
        "target_subtema": "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil",
        "confidence": 1.0,
        "rationale": "Candidíase na díade mãe-bebê (dermatite de fraldas com lesões satélites no lactente e candidíase mamilar na nutriz), exigindo tratamento antifúngico tópico simultâneo para evitar reinfecção."
    },
    # 39: ID 331
    {
        "id": 331,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Icterícia Neonatal e Doenças Hematológicas",
        "confidence": 1.0,
        "rationale": "Crise aplásica em criança com anemia falciforme infectada por Parvovírus B19, com queda aguda da hemoglobina e reticulocitopenia profunda por supressão eritroide transitória."
    },
    # 40: ID 343
    {
        "id": 343,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Acidente escorpiônico moderado/grave em criança com manifestações autonômicas sistêmicas, indicando soroterapia antiescorpiônica imediata antes da transferência hospitalar."
    },
    # 41: ID 347
    {
        "id": 347,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal",
        "confidence": 1.0,
        "rationale": "Herpes neonatal em recém-nascido de 11 dias com vesículas cutâneas, conjuntivite, sepse e apneias, cujo dado epidemiológico materno fundamental é a história de lesões genitais herpéticas na gestação."
    },
    # 42: ID 379
    {
        "id": 379,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Apresentação inicial de Diabetes Mellitus tipo 1 em adolescente sem cetoacidose descompensada; a conduta ambulatorial imediata é o início de insulinoterapia em múltiplas doses diárias."
    },
    # 43: ID 383
    {
        "id": 383,
        "target_area": "Pediatria",
        "target_subtema": "Parasitoses Intestinais: Helmintíases e Protozooses",
        "confidence": 1.0,
        "rationale": "Quadro de diarreia crônica aquosa sem sangue com distensão abdominal e perda ponderal em pré-escolar, típico de giardíase (Giardia lamblia), tratada com metronidazol."
    },
    # 44: ID 384
    {
        "id": 384,
        "target_area": "Pediatria",
        "target_subtema": "Anemias Carenciais e Distúrbios de Micronutrientes (Ferro, Vitamina D)",
        "confidence": 1.0,
        "rationale": "Recomendações científicas da SBP sobre hipovitaminose D na infância e adolescência, destacando períodos de crescimento esquelético acelerado como fases de maior vulnerabilidade."
    },
    # 45: ID 385
    {
        "id": 385,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Manejo da cetoacidose diabética pediátrica na primeira hora: a conduta inicial mandatória antes da insulina é a expansão volêmica vigorosa com soro fisiológico a 20 mL/kg."
    },
    # 46: ID 386
    {
        "id": 386,
        "target_area": "Pediatria",
        "target_subtema": "Calendário Vacinal do PNI e Imunizações Especiais",
        "confidence": 1.0,
        "rationale": "Calendário Nacional de Vacinação do PNI: vacina contra Febre Amarela administrada em esquema aos 9 meses de idade com reforço aos 4 anos."
    },
    # 47: ID 387
    {
        "id": 387,
        "target_area": "Pediatria",
        "target_subtema": "Calendário Vacinal do PNI e Imunizações Especiais",
        "confidence": 1.0,
        "rationale": "Profilaxia da raiva humana pós-exposição pelo PNI: acidente leve com cão domiciliado, sadio e vacinado exige apenas a observação do animal por 10 dias."
    },
    # 48: ID 398
    {
        "id": 398,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Icterícia Neonatal e Doenças Hematológicas",
        "confidence": 1.0,
        "rationale": "Crise de aplasia eritroide pura em criança com anemia falciforme induzida por infecção por Parvovírus B19 (tropismo pelos precursores eritroides na medula óssea)."
    },
    # 49: ID 400
    {
        "id": 400,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Mecanismo hemodinâmico do acidente escorpiônico moderado/grave: tempestade adrenérgica com intensa vasoconstrição periférica levando a convergência das pressões sistólica e diastólica com pulsos finos."
    },
    # 50: ID 401
    {
        "id": 401,
        "target_area": "Pediatria",
        "target_subtema": "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos",
        "confidence": 1.0,
        "rationale": "Investigação radiológica de aspiração/ingestão de corpo estranho radiotransparente na infância; realização de radiografia em pelo menos duas incidências (frontal e perfil) para avaliar sinais indiretos de aprisionamento aéreo."
    },
    # 51: ID 402
    {
        "id": 402,
        "target_area": "Pediatria",
        "target_subtema": "Imunodeficiências, Alergias e Anafilaxia na Infância",
        "confidence": 1.0,
        "rationale": "Quadro clássico de dermatite atópica no lactente, com lesões eczematosas pruriginosas e recidivantes em face, abdome e superfícies extensoras dos membros."
    },
    # 52: ID 403
    {
        "id": 403,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Distúrbio hemorrágico hereditário caracterizado por sangramento mucocutâneo e após ferimentos com petéquias raras, definindo a Doença de Von Willebrand (defeito na hemostasia primária)."
    },
    # 53: ID 404
    {
        "id": 404,
        "target_area": "Pediatria",
        "target_subtema": "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância",
        "confidence": 1.0,
        "rationale": "Tratamento de resgate de estado de mal epiléptico febril prolongado (> 20 min) em criança: uso imediato de benzodiazepínico de ação rápida (midazolam IM/IN/IV)."
    },
    # 54: ID 466
    {
        "id": 466,
        "target_area": "Pediatria",
        "target_subtema": "Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica",
        "confidence": 1.0,
        "rationale": "Choque cardiogênico pediátrico pós-miocardite viral aguda, com disfunção miocárdica, hepatomegalia, linhas B na USG pulmonar e má perfusão periférica; estabilização imediata com inotrópico em BIC."
    },
    # 55: ID 467
    {
        "id": 467,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Púrpura Trombocitopênica Imune (PTI) pediátrica com plaquetopenia isolada e sangramento cutâneo leve (apenas petéquias); conduta expectante com observação e vigilância hematológica."
    },
    # 56: ID 468
    {
        "id": 468,
        "target_area": "Pediatria",
        "target_subtema": "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância",
        "confidence": 1.0,
        "rationale": "Controle de infecção hospitalar em enfermaria pediátrica com bronquiolite viral: isolamento respiratório em quarto privativo com precaução de gotícula para Influenza A e coorte de contato para VSR e Parainfluenza."
    },
    # 57: ID 471
    {
        "id": 471,
        "target_area": "Clínica Médica",
        "target_subtema": "Dermatoses Infecciosas, Hanseníase e Leishmanioses",
        "confidence": 1.0,
        "rationale": "Tratamento da onicomicose em pododáctilo de paciente diabética: terapia antifúngica oral com terbinafina por 12 semanas para erradicação e prevenção de complicações no pé diabético."
    },
    # 58: ID 472
    {
        "id": 472,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Fisiopatologia da peritonite bacteriana espontânea (PBE) na síndrome nefrótica: suscetibilidade a bactérias capsuladas decorrente da perda urinária maciça de imunoglobulinas e fatores do complemento (opsoninas)."
    },
    # 59: ID 474
    {
        "id": 474,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)",
        "confidence": 1.0,
        "rationale": "Quadro clássico de dengue na fase crítica (após defervescência com dor abdominal intensa, vômitos e prova do laço positiva), caracterizado laboratorialmente por hemoconcentração e plaquetopenia severa."
    },
    # 60: ID 511
    {
        "id": 511,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Critérios diagnósticos de debute de Diabetes Mellitus tipo 1 complicado com cetoacidose diabética (glicemia > 200 mg/dL, acidose metabólica com gasometria pH < 7,3/BIC < 15 e cetonúria)."
    },
    # 61: ID 512
    {
        "id": 512,
        "target_area": "Clínica Médica",
        "target_subtema": "Meningites, Encefalites e Infecções do SNC",
        "confidence": 1.0,
        "rationale": "Padrão liquórico característico da meningite viral asséptica em adolescente: predomínio de linfomononucleares, glicose preservada e proteínas normais/pouco aumentadas."
    },
    # 62: ID 513
    {
        "id": 513,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Quadro clínico de Leucemia Linfoide Aguda (LLA) na infância com síndrome de insuficiência medular (anemia, plaquetopenia com petéquias/equimoses) associada a dores ósseas e organomegalia."
    },
    # 63: ID 514
    {
        "id": 514,
        "target_area": "Pediatria",
        "target_subtema": "Parasitoses Intestinais: Helmintíases e Protozooses",
        "confidence": 1.0,
        "rationale": "Síndrome de Löffler (pneumonia eosinofílica e infiltrados pulmonares migratórios causados pelo ciclo pulmonar de larvas de helmintos: Ascaris lumbricoides, Ancylostoma duodenale e Strongyloides stercoralis)."
    },
    # 64: ID 516
    {
        "id": 516,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Emergência oncológica: neutropenia febril pós-quimioterapia em criança com LLA, exigindo colheita de hemoculturas e início imediato de antibioticoterapia antipseudomonas (Cefepima IV)."
    },
    # 65: ID 517
    {
        "id": 517,
        "target_area": "Cirurgia",
        "target_subtema": "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana",
        "confidence": 1.0,
        "rationale": "Disfunção e mau funcionamento de derivação ventrículo-peritoneal (DVP) em lactente com hidrocefalia, manifestando-se por sinais clínicos de hipertensão intracraniana e descontrole de crises epilépticas."
    },
    # 66: ID 585
    {
        "id": 585,
        "target_area": "Pediatria",
        "target_subtema": "Imunodeficiências, Alergias e Anafilaxia na Infância",
        "confidence": 1.0,
        "rationale": "Hipogamaglobulinemia transitória da infância (HTI) em pré-escolar com infecções respiratórias recorrentes autolimitadas, níveis séricos reduzidos de IgG e IgA e linfócitos B preservados."
    },
    # 67: ID 586
    {
        "id": 586,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Propêdêutica da hematúria de origem glomerular (Nefropatia por IgA / glomerulopatia) evidenciada por dismorfismo eritrocitário com acantócitos e proteinúria concomitante."
    },
    # 68: ID 587
    {
        "id": 587,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)",
        "confidence": 1.0,
        "rationale": "Dengue com sinais de alarme (Grupo C) em criança de 7 anos apresentando dor abdominal intensa, vômitos, hepatomegalia, hemoconcentração e plaquetopenia."
    },
    # 69: ID 588
    {
        "id": 588,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Choque cardiogênico induzido por acidente escorpiônico grave com miocardite tóxica aguda, disfunção ventricular, edema agudo de pulmão e tempestade autonômica catecolaminérgica."
    },
    # 70: ID 589
    {
        "id": 589,
        "target_area": "Clínica Médica",
        "target_subtema": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
        "confidence": 1.0,
        "rationale": "Manejo da hipercalemia aguda grave com repercussão eletrocardiográfica no pós-transplante renal; a conduta prioritária é a estabilização de membrana com gluconato de cálcio a 10% EV."
    },
    # 71: ID 590
    {
        "id": 590,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Manejo da PTI (Púrpura Trombocitopênica Imune) aguda na infância sem sangramentos de mucosas ativos; conduta expectante com vigilância ambulatorial seriada."
    },
    # 72: ID 591
    {
        "id": 591,
        "target_area": "Cirurgia",
        "target_subtema": "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana",
        "confidence": 1.0,
        "rationale": "Quadro de lesão expansiva intracraniana (tumor cerebral parietal) em criança manifestando cefaleia com padrão de hipertensão intracraniana matinal, convulsão focal e déficit motor contralateral."
    },
    # 73: ID 614
    {
        "id": 614,
        "target_area": "Pediatria",
        "target_subtema": "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos",
        "confidence": 1.0,
        "rationale": "Ingestão de corpo estranho rombo (moeda) impactado no esôfago superior em lactente sintomático (sialorreia e engasgos); indicação formal de endoscopia digestiva alta de urgência em até 2 horas."
    },
    # 74: ID 615
    {
        "id": 615,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Síndrome de Lise Tumoral (SLT) decorrente de neoplasia hematológica oculta em criança; confirmação laboratorial com dosagem de ácido úrico, fósforo, DHL e potássio séricos."
    },
    # 75: ID 616
    {
        "id": 616,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Síndrome nefrótica atípica na infância (idade > 7 anos, hipertensão arterial grave), necessitando ampliação propedêutica e investigação de causas secundárias antes da corticoterapia empírica isolada."
    },
    # 76: ID 617
    {
        "id": 617,
        "target_area": "Clínica Médica",
        "target_subtema": "Celulite, Erisipela, Osteomielite e Infecções de Partes Moles",
        "confidence": 1.0,
        "rationale": "Quadro clínico de impetigo bolhoso estafilocócico causado por cepas de Staphylococcus aureus produtoras de toxinas esfoliativas, o mesmo agente etiológico da Síndrome da Pele Escaldada Estafilocócica."
    },
    # 77: ID 618
    {
        "id": 618,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Icterícia Neonatal e Doenças Hematológicas",
        "confidence": 1.0,
        "rationale": "Manejo da Síndrome Torácica Aguda (STA) em criança com anemia falciforme: analgesia imediata com opioide endovenoso e repetição urgente de radiografia de tórax."
    },
    # 78: ID 628
    {
        "id": 628,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal",
        "confidence": 1.0,
        "rationale": "Manejo da hidrocefalia obstrutiva progressiva como sequela neurológica de toxoplasmose congênita em lactente jovem, com indicação cirúrgica de derivação ventriculoperitoneal (DVP)."
    },
    # 79: ID 661
    {
        "id": 661,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Tratamento inicial da Glomerulonefrite Pós-Estreptocócica (GNPE) com sobrecarga volêmica, estase jugular e estertores crepitantes: diurético de alça (furosemida) e restrição hidrossalina."
    },
    # 80: ID 662
    {
        "id": 662,
        "target_area": "Pediatria",
        "target_subtema": "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos",
        "confidence": 1.0,
        "rationale": "Ingestão de corpo estranho esofágico em criança com sialorreia e impactação mecânica da deglutição; indicação de endoscopia digestiva alta de urgência para remoção."
    },
    # 81: ID 663
    {
        "id": 663,
        "target_area": "Pediatria",
        "target_subtema": "Neonatologia: Icterícia Neonatal e Doenças Hematológicas",
        "confidence": 1.0,
        "rationale": "Crise de sequestro esplênico em criança de 2 anos com anemia falciforme, manifestando-se por esplenomegalia maciça aguda, choque hipovolêmico, queda grave da hemoglobina e reticulocitose compensatória."
    },
    # 82: ID 664
    {
        "id": 664,
        "target_area": "Clínica Médica",
        "target_subtema": "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base",
        "confidence": 1.0,
        "rationale": "Acidose metabólica com ânion gap aumentado (AG = 22 mEq/L) secundária à hiperlactatemia tecidual em paciente pediátrico em choque séptico de foco cutâneo."
    },
    # 83: ID 665
    {
        "id": 665,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Coagulopatia congênita com alargamento isolado do Tempo de Protrombina (TP/INR) e TTPA normal, patognomônico de deficiência congênita do Fator VII da coagulação."
    },
    # 84: ID 666
    {
        "id": 666,
        "target_area": "Pediatria",
        "target_subtema": "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância",
        "confidence": 1.0,
        "rationale": "Manejo de manutenção da asma não controlada em escolar (Etapa 3 da GINA para 6-11 anos): associação de corticoide inalatório e beta-2 agonista de longa ação (LABA)."
    },
    # 85: ID 667
    {
        "id": 667,
        "target_area": "Clínica Médica",
        "target_subtema": "Leucemias, Linfomas e Mieloma Múltiplo",
        "confidence": 1.0,
        "rationale": "Investigação diagnóstica de Leucemia Linfoide Aguda (LLA) em escolar com dores osteoarticulares noturnas progressivas, perda de peso, linfadenopatia e citopenias; indicação mandatória de mielograma."
    },
    # 86: ID 678
    {
        "id": 678,
        "target_area": "Clínica Médica",
        "target_subtema": "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares",
        "confidence": 1.0,
        "rationale": "Síndrome de Guillain-Barré pós-gastroenterite infecciosa em pré-escolar (paralisia flácida e arreflexia de MMII); confirmação pelo achado de dissociação albuminocitológica no líquido cefalorraquidiano."
    },
    # 87: ID 679
    {
        "id": 679,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Critérios clínicos e laboratoriais de alta hospitalar em paciente pediátrico com síndrome nefrótica após reversão da sobrecarga e restauração da diurese e estabilidade clínica."
    },
    # 88: ID 680
    {
        "id": 680,
        "target_area": "Clínica Médica",
        "target_subtema": "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia",
        "confidence": 1.0,
        "rationale": "Protocolo de emergência em hemofilia A grave pós-trauma cranioencefálico com vômitos: reposição imediata de Fator VIII para correção a 100% precedendo qualquer exame de neuroimagem."
    },
    # 89: ID 681
    {
        "id": 681,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Emergência nefrológica: GNPE complicada com lesão renal aguda oligoanúrica, hipertensão grave e hipercalemia com alteração de ECG; manejo prioritário com gluconato de cálcio, furosemida e restrição hídrica."
    },
    # 90: ID 701
    {
        "id": 701,
        "target_area": "Clínica Médica",
        "target_subtema": "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas",
        "confidence": 1.0,
        "rationale": "Diagnóstico do HIV em crianças maiores de 18 meses expostas verticalmente: teste sorológico isolado reagente com antecedentes de carga viral indetectável exige repetição após 1 mês para afastar falso-positivo."
    },
    # 91: ID 702
    {
        "id": 702,
        "target_area": "Clínica Médica",
        "target_subtema": "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento",
        "confidence": 1.0,
        "rationale": "Diabetes monogênico tipo MODY (Maturity-Onset Diabetes of the Young) em adolescente magra e assintomática com autoanticorpos negativos e herança autossômica dominante; indicação de dieta e teste genético."
    },
    # 92: ID 703
    {
        "id": 703,
        "target_area": "Pediatria",
        "target_subtema": "Imunodeficiências, Alergias e Anafilaxia na Infância",
        "confidence": 1.0,
        "rationale": "Imunodeficiência Combinada Grave (SCID) detectada na triagem neonatal; contraindicação absoluta a todas as vacinas com vírus ou bactérias vivos atenuados devido ao risco de disseminação fatal."
    },
    # 93: ID 704
    {
        "id": 704,
        "target_area": "Clínica Médica",
        "target_subtema": "Diagnóstico Diferencial das Anemias e Hemoglobinopatias",
        "confidence": 1.0,
        "rationale": "Diagnóstico diferencial das anemias microcíticas: microcitose intensa desproporcional à anemia com eritrocitose e RDW normal é típica de traço talassêmico, investigado por eletroforese de hemoglobina."
    },
    # 94: ID 705
    {
        "id": 705,
        "target_area": "Pediatria",
        "target_subtema": "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas",
        "confidence": 1.0,
        "rationale": "Enteropatia perdedora de proteínas por Linfangiectasia Intestinal primária congênita, caracterizada por diarreia crônica, hipoalbuminemia, linfopenia, hipogamaglobulinemia e alfa-1-antitripsina fecal elevada."
    },
    # 95: ID 706
    {
        "id": 706,
        "target_area": "Clínica Médica",
        "target_subtema": "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias",
        "confidence": 1.0,
        "rationale": "Dermatomiosite juvenil em criança de 8 anos manifestando fraqueza muscular proximal e simétrica de cinturas (dificuldade para subir escadas e elevar braços) associada a lesões cutâneas típicas."
    },
    # 96: ID 707
    {
        "id": 707,
        "target_area": "Pediatria",
        "target_subtema": "Imunodeficiências, Alergias e Anafilaxia na Infância",
        "confidence": 1.0,
        "rationale": "Deficiência congênita do sistema complemento (componentes terminais C5 a C9) manifestada por episódios recorrentes de doença meningocócica invasiva por Neisseria meningitidis."
    },
    # 97: ID 708
    {
        "id": 708,
        "target_area": "Clínica Médica",
        "target_subtema": "Toxicologia Clínica e Acidentes por Animais Peçonhentos",
        "confidence": 1.0,
        "rationale": "Manejo do choque cardiogênico pós-acidente escorpiônico grave com disfunção miocárdica pós-soroterapia: indicação imediata de inotrópico positivo com dobutamina em infusão contínua."
    },
    # 98: ID 709
    {
        "id": 709,
        "target_area": "Clínica Médica",
        "target_subtema": "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias",
        "confidence": 1.0,
        "rationale": "Tratamento de suporte na Síndrome Hemolítico-Urêmica (SHU) em lactente com anemia hemolítica microangiopática grave (Hb 6,0 g/dL) sintomática: transfusão cuidadosa de concentrado de hemácias."
    },
    # 99: ID 710
    {
        "id": 710,
        "target_area": "Pediatria",
        "target_subtema": "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância",
        "confidence": 1.0,
        "rationale": "Fatores de risco para recorrência de crise febril na infância: história familiar de crise febril em parente de primeiro grau (como irmão) é um dos principais determinantes de recorrência."
    }
]

# Validar que todos os 100 itens correspondem a temas canônicos
with open("ped_b1.json", "r", encoding="utf-8") as f:
    orig_data = json.load(f)

assert len(classifications) == len(orig_data), f"Tamanho divergente: {len(classifications)} vs {len(orig_data)}"

errors = []
for idx, (orig, item) in enumerate(zip(orig_data, classifications)):
    if orig["id"] != item["id"]:
        errors.append(f"Mismatch no índice {idx}: orig ID {orig['id']} vs class ID {item['id']}")
    a = item["target_area"]
    s = item["target_subtema"]
    if a not in TAX_170:
        errors.append(f"Área inválida: {a} para ID {item['id']}")
    elif s not in TAX_170[a]:
        errors.append(f"Subtema inválido: {s} na área {a} para ID {item['id']}")

if errors:
    print("ERROS ENCONTRADOS:")
    for err in errors:
        print(" -", err)
    sys.exit(1)
else:
    print(f"Sucesso: Todas as {len(classifications)} classificações estão alinhadas 1:1 com ped_b1.json e são 100% canônicas!")
    with open("ped_b1_classified.json", "w", encoding="utf-8") as f:
        json.dump(classifications, f, ensure_ascii=False, indent=2)
    print("Arquivo 'ped_b1_classified.json' gravado com sucesso.")

