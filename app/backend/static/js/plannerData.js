/**
 * Currículo de Estudos — Residência Médica (Acesso Direto R1)
 * Foco USP (HC-FMUSP / HCRP / HRAC) e demais faculdades paulistas.
 *
 * 80 temas cobrindo as 5 grandes áreas de forma completa.
 * O planejador inteligente (app.js) encaixa estes temas no seu calendário real
 * entre a data de início e a data da prova, ajustando o ritmo automaticamente.
 *
 * Campos:
 *   week      -> ordem sequencial de estudo
 *   area      -> uma das 5 áreas (usada para badge e para filtrar questões)
 *   theme     -> título do tema
 *   highYield -> true para temas de altíssimo rendimento na USP
 *   details   -> pontos-chave cobrados
 */

window.PLANNER_WEEKS = [

  // ═══════════════ MEDICINA PREVENTIVA E SAÚDE COLETIVA ═══════════════
  {
    week: 1,
    area: "Medicina Preventiva",
    theme: "Transição Demográfica/Epidemiológica e Indicadores de Saúde",
    highYield: true,
    dbSubtemas: ["Transição Demográfica e Epidemiológica", "Indicadores de Saúde"],
    details: [
      "Transição demográfica (envelhecimento, queda de fecundidade, pirâmide etária) e transição epidemiológica (tripla carga de doenças)",
      "Indicadores de mortalidade: coeficiente de mortalidade geral, infantil, neonatal, materna e razão de mortalidade materna",
      "Indicadores de morbidade: incidência, prevalência, letalidade; padronização de taxas",
      "Esperança de vida, anos potenciais de vida perdidos e DALY"
    ]
  },
  {
    week: 2,
    area: "Medicina Preventiva",
    theme: "História das Políticas de Saúde e Reforma Sanitária",
    highYield: false,
    dbSubtemas: ["Modelos de Atenção e Reforma Sanitária"],
    details: [
      "Do modelo sanitarista-campanhista e previdenciário (INAMPS) ao SUS",
      "8ª Conferência Nacional de Saúde (1986) e o Movimento da Reforma Sanitária",
      "Constituição de 1988: saúde como direito de todos e dever do Estado",
      "Modelos de atenção à saúde e determinantes sociais da saúde (Dahlgren e Whitehead)"
    ]
  },
  {
    week: 3,
    area: "Medicina Preventiva",
    theme: "Princípios do SUS e Atenção Primária à Saúde",
    highYield: true,
    dbSubtemas: ["Princípios e Diretrizes do SUS", "Atenção Primária à Saúde", "Ferramentas da APS (SOAP, PTS, Método Centrado na Pessoa)"],
    details: [
      "Princípios doutrinários: universalidade, integralidade e equidade",
      "Princípios organizativos: descentralização, regionalização, hierarquização, participação popular",
      "Atributos da APS (Starfield): primeiro contato, longitudinalidade, integralidade, coordenação",
      "Política Nacional de Atenção Básica (PNAB) e Estratégia Saúde da Família (eSF, eAP, NASF)"
    ]
  },
  {
    week: 4,
    area: "Medicina Preventiva",
    theme: "Legislação, Financiamento e Controle Social do SUS",
    highYield: false,
    dbSubtemas: ["Legislação e Financiamento do SUS", "Controle Social e Participação Popular"],
    details: [
      "Lei 8.080/90 (organização e funcionamento) e Lei 8.142/90 (participação e financiamento)",
      "Conselhos de Saúde (permanentes, paritários, deliberativos) vs Conferências (a cada 4 anos)",
      "Financiamento tripartite, blocos de financiamento e emenda constitucional do piso da saúde",
      "Pacto pela Saúde, Decreto 7.508/2011, COAP e comissões intergestores (CIT, CIB, CIR)"
    ]
  },
  {
    week: 5,
    area: "Medicina Preventiva",
    theme: "Redes de Atenção e Sistemas de Informação em Saúde",
    highYield: false,
    dbSubtemas: ["Redes de Atenção à Saúde", "Sistemas de Informação em Saúde"],
    details: [
      "Redes de Atenção à Saúde (RAS): APS como coordenadora e ordenadora do cuidado",
      "Sistemas de informação: SIM (mortalidade), SINASC (nascidos vivos), SINAN (agravos), SIH, SIA, e-SUS",
      "Declaração de óbito e declaração de nascido vivo: preenchimento e fluxo",
      "Redes temáticas: Cegonha, Urgência e Emergência, RAPS (saúde mental)"
    ]
  },
  {
    week: 6,
    area: "Medicina Preventiva",
    theme: "Vigilância em Saúde e Notificação Compulsória",
    highYield: true,
    dbSubtemas: ["Vigilância em Saúde e Notificação Compulsória", "Vigilância Sanitária"],
    details: [
      "Vigilância epidemiológica, sanitária, ambiental e saúde do trabalhador",
      "Lista Nacional de Notificação Compulsória: notificação imediata (24h) vs semanal",
      "Investigação de surtos e epidemias; curva epidêmica; medidas de controle e bloqueio",
      "Endemia, epidemia, pandemia; níveis endêmicos e canal endêmico"
    ]
  },
  {
    week: 7,
    area: "Medicina Preventiva",
    theme: "Delineamentos de Estudos Epidemiológicos",
    highYield: true,
    dbSubtemas: ["Estudos Observacionais (Coorte, Caso-Controle, Transversal, Ecológico)", "Ensaios Clínicos e Randomização"],
    details: [
      "Observacionais: coorte, caso-controle, transversal e ecológico (vantagens, desvantagens, vieses)",
      "Experimentais: ensaio clínico randomizado, cegamento, intenção de tratar",
      "Medidas de associação: Risco Relativo, Odds Ratio, Razão de Prevalência",
      "Vieses de seleção, aferição e confusão; hierarquia das evidências"
    ]
  },
  {
    week: 8,
    area: "Medicina Preventiva",
    theme: "Bioestatística, Testes Diagnósticos e MBE",
    highYield: true,
    dbSubtemas: ["Bioestatística e Testes de Hipótese", "Testes Diagnósticos (Sensibilidade, VPP, ROC)", "Medicina Baseada em Evidências", "Medidas de Associação e Impacto (RR, OR, NNT)"],
    details: [
      "Sensibilidade, especificidade, valor preditivo positivo/negativo e influência da prevalência",
      "Razão de verossimilhança, curva ROC e ponto de corte",
      "Medidas de impacto: risco atribuível, redução absoluta/relativa de risco, NNT e NNH",
      "Testes de hipótese: valor-p, intervalo de confiança, erros tipo I e II, poder do estudo"
    ]
  },
  {
    week: 9,
    area: "Medicina Preventiva",
    theme: "Níveis de Prevenção, Rastreamento e Prevenção Quaternária",
    highYield: false,
    dbSubtemas: ["Níveis de Prevenção e Prevenção Quaternária", "Rastreamento Populacional"],
    details: [
      "Níveis de prevenção de Leavell & Clark (primária, secundária, terciária) e prevenção quaternária",
      "Critérios de Wilson e Jungner para rastreamento populacional",
      "Vieses do rastreamento: lead time, length time e sobrediagnóstico",
      "Principais programas de rastreamento no Brasil (colo de útero, mama, e outros)"
    ]
  },
  {
    week: 10,
    area: "Medicina Preventiva",
    theme: "Saúde Ocupacional e do Trabalhador",
    highYield: true,
    dbSubtemas: ["Saúde Ocupacional e do Trabalhador"],
    details: [
      "Classificação de Schilling (I: causa necessária; II: fator contributivo; III: agravante)",
      "Pneumoconioses (silicose, asbestose, antracose) — clínica e achados radiológicos",
      "LER/DORT, PAIR (perda auditiva induzida por ruído) e transtornos mentais no trabalho",
      "Acidente de trabalho com material biológico: profilaxia pós-exposição e CAT"
    ]
  },
  {
    week: 11,
    area: "Medicina Preventiva",
    theme: "Ética Médica, Bioética e Documentos Médicos",
    highYield: false,
    dbSubtemas: ["Ética Médica e Bioética"],
    details: [
      "Princípios da bioética: autonomia, beneficência, não-maleficência e justiça",
      "Sigilo médico, consentimento informado e autonomia do paciente/menor",
      "Atestados, declarações e prontuário; responsabilidade civil e ética",
      "Diretrizes antecipadas de vontade, terminalidade e ortotanásia"
    ]
  },

  // ═══════════════ PEDIATRIA ═══════════════
  {
    week: 12,
    area: "Pediatria",
    theme: "Crescimento e Desenvolvimento Infantil",
    highYield: true,
    dbSubtemas: ["Crescimento e Desenvolvimento"],
    details: [
      "Curvas de crescimento da OMS (escore Z e percentil para peso, estatura e perímetro cefálico)",
      "Causas de baixa estatura (familiar, atraso constitucional, patológicas)",
      "Marcos do desenvolvimento neuropsicomotor (motor, cognitivo, linguagem, social)",
      "Sinais de alerta para transtorno do espectro autista e atraso global do desenvolvimento"
    ]
  },
  {
    week: 13,
    area: "Pediatria",
    theme: "Aleitamento Materno e Alimentação Complementar",
    highYield: true,
    dbSubtemas: ["Aleitamento Materno e Alimentação"],
    details: [
      "Vantagens do aleitamento; contraindicações formais (HIV, HTLV) e temporárias",
      "Composição do leite (colostro, transição, maduro) e tipos de amamentação",
      "Manejo de intercorrências: fissuras, ingurgitamento, mastite, baixa produção",
      "Introdução alimentar (a partir dos 6 meses) e suplementação de ferro e vitamina D"
    ]
  },
  {
    week: 14,
    area: "Pediatria",
    theme: "Imunização — Calendário Nacional (PNI)",
    highYield: true,
    dbSubtemas: ["Imunização (PNI)"],
    details: [
      "Esquema do primeiro ano de vida (BCG, hepatite B, penta, VIP/VOP, pneumo, rota, meningo)",
      "Vacinas de vírus vivos vs inativados e contraindicações específicas",
      "Eventos adversos pós-vacinais e conduta",
      "Situações especiais: prematuros, imunodeprimidos, gestantes e comunicantes"
    ]
  },
  {
    week: 15,
    area: "Pediatria",
    theme: "Triagem Neonatal e Cuidados com o Recém-Nascido",
    highYield: false,
    dbSubtemas: ["Triagem Neonatal e Cuidados com o Recém-Nascido"],
    details: [
      "Testes de triagem: pezinho (biológico), orelhinha (auditivo), olhinho (reflexo vermelho), coraçãozinho (oximetria)",
      "Doenças triadas no teste do pezinho (hipotireoidismo congênito, fenilcetonúria, anemia falciforme e outras)",
      "Cuidados de rotina na sala de parto e alojamento conjunto",
      "Avaliação da idade gestacional (Capurro, New Ballard) e classificação do RN (PIG/AIG/GIG)"
    ]
  },
  {
    week: 16,
    area: "Pediatria",
    theme: "Neonatologia: Reanimação e Distúrbios Respiratórios do RN",
    highYield: true,
    dbSubtemas: ["Reanimação Neonatal", "Distúrbios Respiratórios do Recém-Nascido", "Sepse Neonatal"],
    details: [
      "Fluxograma de reanimação neonatal da SBP (RN ≥34 sem e <34 sem)",
      "Síndrome do desconforto respiratório (doença da membrana hialina) e uso de surfactante",
      "Taquipneia transitória do RN e síndrome de aspiração meconial",
      "Sepse neonatal precoce e tardia: fatores de risco, clínica e conduta"
    ]
  },
  {
    week: 17,
    area: "Pediatria",
    theme: "Icterícia Neonatal e Infecções Congênitas",
    highYield: true,
    dbSubtemas: ["Icterícia Neonatal", "Infecções Congênitas (STORCH e Sífilis)"],
    details: [
      "Icterícia fisiológica vs patológica; incompatibilidade ABO e Rh",
      "Indicações de fototerapia e exsanguineotransfusão; kernicterus",
      "Infecções congênitas (STORCH): sífilis, toxoplasmose, rubéola, CMV, Zika",
      "Rastreamento, achados clínicos e conduta na sífilis congênita"
    ]
  },
  {
    week: 18,
    area: "Pediatria",
    theme: "Diarreia Aguda, Reidratação e Distúrbios Hidroeletrolíticos",
    highYield: true,
    dbSubtemas: ["Diarreia Aguda e Reidratação", "Distúrbios Hidroeletrolíticos e Fluidoterapia"],
    details: [
      "Fisiopatologia da diarreia (osmótica, secretora, invasiva) e principais agentes",
      "Avaliação do estado de hidratação e Planos A, B e C do Ministério da Saúde",
      "Distúrbios do sódio na desidratação; hidratação parenteral (Holliday-Segar)",
      "Uso de zinco, probióticos e indicações de antibiótico na diarreia infantil"
    ]
  },
  {
    week: 19,
    area: "Pediatria",
    theme: "Infecções Respiratórias Agudas e Asma na Infância",
    highYield: true,
    dbSubtemas: ["Infecções Respiratórias Agudas (Pneumonia, Bronquiolite, Crupe)", "Asma na Infância"],
    details: [
      "Pneumonias por faixa etária (etiologia, clínica, critérios de internação, antibiótico)",
      "Bronquiolite viral aguda (VSR): diagnóstico clínico e manejo de suporte",
      "Crupe viral, epiglotite e laringites; otite média aguda e sinusite",
      "Diagnóstico e tratamento de manutenção e crise da asma na criança"
    ]
  },
  {
    week: 20,
    area: "Pediatria",
    theme: "Doenças Exantemáticas e Doença de Kawasaki",
    highYield: true,
    dbSubtemas: ["Doenças Exantemáticas", "Kawasaki e Vasculites (Henoch-Schönlein)"],
    details: [
      "Sarampo, rubéola, eritema infeccioso, exantema súbito, escarlatina e varicela",
      "Período de incubação, pródromo e progressão do exantema de cada doença",
      "Doença de Kawasaki: critérios diagnósticos, risco de aneurisma coronariano e tratamento (IVIG + AAS)",
      "Complicações e profilaxia pós-exposição"
    ]
  },
  {
    week: 21,
    area: "Pediatria",
    theme: "Parasitoses, Anemias e Verminoses na Infância",
    highYield: false,
    dbSubtemas: ["Parasitoses e Verminoses", "Anemias na Infância"],
    details: [
      "Anemia ferropriva: rastreamento, profilaxia e tratamento; anemias hemolíticas na criança",
      "Principais helmintíases (ascaridíase, ancilostomíase, enterobíase, teníase) e protozooses (giardíase, amebíase)",
      "Ciclos, clínica e tratamento antiparasitário",
      "Larva migrans, estrongiloidíase e esquistossomose"
    ]
  },
  {
    week: 22,
    area: "Pediatria",
    theme: "Desnutrição, Obesidade e Distúrbios Nutricionais",
    highYield: false,
    dbSubtemas: ["Desnutrição e Obesidade Infantil"],
    details: [
      "Desnutrição energético-proteica: marasmo, kwashiorkor e manejo das complicações",
      "Obesidade infantil: diagnóstico (IMC/idade), comorbidades e abordagem",
      "Deficiências de micronutrientes (vitamina A, D, ferro, zinco, iodo)",
      "Distúrbios do crescimento associados à nutrição"
    ]
  },
  {
    week: 23,
    area: "Pediatria",
    theme: "Cardiopatias Congênitas e Sopros na Infância",
    highYield: false,
    dbSubtemas: ["Cardiopatias Congênitas"],
    details: [
      "Sopro inocente vs patológico; sinais de alerta",
      "Cardiopatias acianóticas (CIV, CIA, PCA, coarctação de aorta)",
      "Cardiopatias cianóticas (Tetralogia de Fallot, transposição de grandes vasos)",
      "Rastreamento por oximetria e conduta inicial no RN cianótico"
    ]
  },
  {
    week: 24,
    area: "Pediatria",
    theme: "Nefro-urologia Pediátrica",
    highYield: false,
    dbSubtemas: ["Infecção do Trato Urinário e Refluxo", "Glomerulopatias na Infância (Nefrótica, Nefrítica, SHU)"],
    details: [
      "Infecção do trato urinário na criança: diagnóstico, tratamento e investigação de imagem",
      "Refluxo vesicoureteral e bexiga neurogênica",
      "Síndrome nefrótica (lesões mínimas) vs síndrome nefrítica (GNPE)",
      "Glomerulonefrite difusa aguda pós-estreptocócica: clínica e evolução"
    ]
  },
  {
    week: 25,
    area: "Pediatria",
    theme: "Emergências Pediátricas, Convulsão Febril e PALS",
    highYield: false,
    dbSubtemas: ["Convulsão Febril e Emergências Neurológicas", "Parada Cardiorrespiratória Pediátrica (PALS)", "Cetoacidose Diabética na Infância"],
    details: [
      "Crise convulsiva febril simples vs complexa: conduta e investigação",
      "Suporte básico e avançado de vida em pediatria (PALS) e reconhecimento de choque",
      "Traumatismo cranioencefálico (regras do PECARN para TC)",
      "Cetoacidose diabética, anafilaxia e intoxicações na criança"
    ]
  },
  {
    week: 26,
    area: "Pediatria",
    theme: "Maus-Tratos, Adolescência e Puberdade",
    highYield: false,
    dbSubtemas: ["Maus-tratos e Violência", "Adolescência e Puberdade"],
    details: [
      "Identificação de maus-tratos (físico, sexual, negligência) e notificação/Conselho Tutelar",
      "Estágios de Tanner e sequência normal da puberdade em meninos e meninas",
      "Puberdade precoce e atraso puberal",
      "Confidencialidade, sexualidade e saúde do adolescente"
    ]
  },

  // ═══════════════ GINECOLOGIA E OBSTETRÍCIA ═══════════════
  {
    week: 27,
    area: "Ginecologia e Obstetrícia",
    theme: "Ciclo Menstrual e Fisiologia Hormonal",
    highYield: true,
    dbSubtemas: ["Ciclo Menstrual e Fisiologia Hormonal"],
    details: [
      "Eixo hipotálamo-hipófise-ovário e fases folicular, ovulatória e lútea",
      "Ações de FSH, LH, estrogênio e progesterona ao longo do ciclo",
      "Ciclo endometrial: proliferativo, secretor e menstruação",
      "Puberdade feminina, telarca, pubarca e menarca"
    ]
  },
  {
    week: 28,
    area: "Ginecologia e Obstetrícia",
    theme: "Anticoncepção e Planejamento Familiar",
    highYield: true,
    dbSubtemas: ["Anticoncepção e Planejamento Familiar"],
    details: [
      "Métodos combinados e de progestagênio isolado: indicações e efeitos adversos",
      "Critérios de Elegibilidade da OMS (categorias 1 a 4)",
      "LARC: DIU de cobre, DIU de levonorgestrel e implante",
      "Contracepção de emergência e métodos definitivos"
    ]
  },
  {
    week: 29,
    area: "Ginecologia e Obstetrícia",
    theme: "Amenorreia, SOP e Hiperandrogenismo",
    highYield: false,
    dbSubtemas: ["Amenorreia e Síndrome dos Ovários Policísticos"],
    details: [
      "Amenorreia primária e secundária: investigação por compartimentos",
      "Síndrome dos ovários policísticos: critérios de Rotterdam e manejo",
      "Hiperprolactinemia e insuficiência ovariana prematura",
      "Hirsutismo e diagnóstico diferencial do hiperandrogenismo"
    ]
  },
  {
    week: 30,
    area: "Ginecologia e Obstetrícia",
    theme: "Sangramento Uterino Anormal, Miomatose e Endometriose",
    highYield: false,
    dbSubtemas: ["Sangramento Uterino Anormal e Miomatose", "Endometriose"],
    details: [
      "Classificação PALM-COEIN do sangramento uterino anormal",
      "Leiomioma uterino: classificação FIGO, clínica e tratamento",
      "Endometriose: fisiopatologia, dor pélvica, infertilidade e tratamento",
      "Adenomiose e pólipos endometriais"
    ]
  },
  {
    week: 31,
    area: "Ginecologia e Obstetrícia",
    theme: "Vulvovaginites, IST e Doença Inflamatória Pélvica",
    highYield: true,
    dbSubtemas: ["Vulvovaginites e Cervicites", "Doença Inflamatória Pélvica e IST"],
    details: [
      "Vaginose bacteriana, candidíase e tricomoníase (critérios de Amsel, pH, microscopia)",
      "Cervicites por clamídia e gonococo; abordagem sindrômica das IST",
      "Sífilis, herpes genital, cancro mole, HPV e donovanose",
      "Doença inflamatória pélvica: critérios diagnósticos, tratamento e complicações"
    ]
  },
  {
    week: 32,
    area: "Ginecologia e Obstetrícia",
    theme: "Climatério e Terapia Hormonal",
    highYield: false,
    dbSubtemas: ["Climatério e Terapia Hormonal"],
    details: [
      "Transição menopáusica e diagnóstico da menopausa",
      "Indicações e contraindicações da terapia de reposição hormonal",
      "Esquemas de TRH (estrogênio isolado vs combinado) e riscos",
      "Manejo não hormonal dos sintomas e rastreamento de osteoporose"
    ]
  },
  {
    week: 33,
    area: "Ginecologia e Obstetrícia",
    theme: "Rastreamento e Câncer de Colo Uterino",
    highYield: true,
    dbSubtemas: ["Rastreamento e Câncer de Colo Uterino"],
    details: [
      "Rastreamento com citologia (Papanicolau): idade de início e periodicidade",
      "Conduta nas alterações citológicas (ASC-US, LSIL, ASC-H, HSIL, AGC)",
      "Colposcopia, biópsia e tratamento das lesões precursoras (NIC)",
      "Papel do HPV, vacinação e estadiamento do câncer de colo"
    ]
  },
  {
    week: 34,
    area: "Ginecologia e Obstetrícia",
    theme: "Mastologia: Rastreamento, Nódulos e Câncer de Mama",
    highYield: true,
    dbSubtemas: ["Mastologia e Câncer de Mama"],
    details: [
      "Rastreamento mamográfico: idade, periodicidade e classificação BI-RADS",
      "Nódulos benignos (fibroadenoma, cisto) vs sinais de malignidade",
      "Investigação do nódulo (tríade diagnóstica) e derrame papilar",
      "Fatores de risco, tipos histológicos e princípios do tratamento do câncer de mama"
    ]
  },
  {
    week: 35,
    area: "Ginecologia e Obstetrícia",
    theme: "Câncer de Endométrio, Ovário e Incontinência/Distopias",
    highYield: false,
    dbSubtemas: ["Câncer de Endométrio e Ovário", "Incontinência Urinária e Prolapsos"],
    details: [
      "Câncer de endométrio: fatores de risco, sangramento pós-menopausa e investigação",
      "Câncer de ovário: tipos, marcadores e apresentação tardia",
      "Incontinência urinária de esforço vs de urgência: diagnóstico e tratamento",
      "Distopias genitais (prolapsos): classificação POP-Q e conduta"
    ]
  },
  {
    week: 36,
    area: "Ginecologia e Obstetrícia",
    theme: "Assistência Pré-Natal de Baixo e Alto Risco",
    highYield: true,
    dbSubtemas: ["Assistência Pré-natal", "Gestação de Alto Risco"],
    details: [
      "Exames de rotina por trimestre e cálculo da idade gestacional/DPP",
      "Suplementação de ácido fólico e ferro; ganho de peso na gestação",
      "Vacinação na gestação (dTpa, hepatite B, influenza) e contraindicadas",
      "Rastreamento de Streptococcus do grupo B e profilaxia intraparto"
    ]
  },
  {
    week: 37,
    area: "Ginecologia e Obstetrícia",
    theme: "Mecanismo e Assistência ao Parto",
    highYield: true,
    dbSubtemas: ["Mecanismo e Assistência ao Parto"],
    details: [
      "Tempos do mecanismo de parto (insinuação, descida, rotação, desprendimento)",
      "Fases clínicas do parto e uso/interpretação do partograma",
      "Distocias funcionais, de trajeto e de apresentação; indicações de cesárea e fórceps",
      "Analgesia de parto e assistência ao período expulsivo"
    ]
  },
  {
    week: 38,
    area: "Ginecologia e Obstetrícia",
    theme: "Síndromes Hipertensivas da Gestação",
    highYield: true,
    dbSubtemas: ["Síndromes Hipertensivas da Gestação"],
    details: [
      "Classificação: HAS crônica, pré-eclâmpsia, eclâmpsia e sobreposta",
      "Critérios de gravidade e iminência de eclâmpsia",
      "Sulfato de magnésio (Zuspan/Pritchard), toxicidade e antídoto (gluconato de cálcio)",
      "Síndrome HELLP: diagnóstico laboratorial e conduta"
    ]
  },
  {
    week: 39,
    area: "Ginecologia e Obstetrícia",
    theme: "Diabetes e Outras Intercorrências Clínicas da Gestação",
    highYield: false,
    dbSubtemas: ["Diabetes Gestacional", "Infecções na Gestação (HIV, Sífilis, STORCH)"],
    details: [
      "Diabetes gestacional: rastreamento, TOTG 75g e metas de controle",
      "Diabetes pré-gestacional e repercussões fetais",
      "Infecção urinária, bacteriúria assintomática e pielonefrite na gestação",
      "Transmissão vertical do HIV, hepatites e sífilis"
    ]
  },
  {
    week: 40,
    area: "Ginecologia e Obstetrícia",
    theme: "Hemorragias da Primeira Metade da Gestação",
    highYield: true,
    dbSubtemas: ["Abortamento e Doença Trofoblástica", "Gestação Ectópica"],
    details: [
      "Abortamento (ameaça, completo, incompleto, retido, infectado): clínica e conduta",
      "Gravidez ectópica: diagnóstico e critérios para metotrexato vs cirurgia",
      "Doença trofoblástica gestacional (mola completa vs parcial) e seguimento com beta-hCG",
      "Diagnóstico diferencial por ultrassom e dosagens de beta-hCG"
    ]
  },
  {
    week: 41,
    area: "Ginecologia e Obstetrícia",
    theme: "Hemorragias da Segunda Metade e Prematuridade",
    highYield: true,
    dbSubtemas: ["Hemorragias da 2ª Metade (DPP, Placenta Prévia)", "Trabalho de Parto Prematuro e Rotura de Membranas"],
    details: [
      "Descolamento prematuro de placenta vs placenta prévia: quadro e conduta",
      "Rotura uterina e rotura de vasa prévia",
      "Trabalho de parto prematuro: tocólise e corticoterapia antenatal",
      "Amniorrexe prematura: diagnóstico, riscos e conduta conforme idade gestacional"
    ]
  },
  {
    week: 42,
    area: "Ginecologia e Obstetrícia",
    theme: "Vitalidade Fetal, RCF e Puerpério",
    highYield: false,
    dbSubtemas: ["Vitalidade Fetal e Restrição de Crescimento", "Puerpério e Hemorragia Pós-parto", "Infecção Puerperal"],
    details: [
      "Avaliação da vitalidade fetal: cardiotocografia, perfil biofísico e Doppler",
      "Restrição de crescimento fetal: classificação e dopplerfluxometria",
      "Puerpério fisiológico e patológico; hemorragia pós-parto (4 T) e atonia uterina",
      "Infecção puerperal e mastite puerperal"
    ]
  },

  // ═══════════════ CIRURGIA GERAL ═══════════════
  {
    week: 43,
    area: "Cirurgia Geral",
    theme: "Avaliação Pré-Operatória e Risco Cirúrgico",
    highYield: false,
    dbSubtemas: ["Avaliação Pré-operatória e Risco Cirúrgico"],
    details: [
      "Classificação ASA e índice de risco cardíaco revisado (Lee)",
      "Manejo perioperatório de anticoagulantes, antiagregantes, hipoglicemiantes e anti-hipertensivos",
      "Jejum pré-operatório e profilaxia de TEV (escore de Caprini)",
      "Avaliação pulmonar e do paciente diabético/renal"
    ]
  },
  {
    week: 44,
    area: "Cirurgia Geral",
    theme: "Resposta Metabólica ao Trauma e Pós-Operatório",
    highYield: true,
    dbSubtemas: ["Resposta Metabólica ao Trauma e Pós-operatório"],
    details: [
      "Fases da resposta metabólica ao trauma (hormônios contrarreguladores e citocinas)",
      "Febre pós-operatória: causas conforme o tempo (24h, 72h, tardia)",
      "Complicações pós-operatórias: íleo, deiscência, fístulas e abscessos",
      "Nutrição perioperatória e reabilitação (ERAS/ACERTO)"
    ]
  },
  {
    week: 45,
    area: "Cirurgia Geral",
    theme: "Cicatrização, Infecção de Sítio Cirúrgico e Suturas",
    highYield: false,
    dbSubtemas: ["Infecção de Sítio Cirúrgico e Cicatrização"],
    details: [
      "Fases da cicatrização e fatores que a prejudicam",
      "Classificação das feridas operatórias e profilaxia antibiótica cirúrgica",
      "Infecção de sítio cirúrgico: diagnóstico e conduta",
      "Fios de sutura (absorvíveis/inabsorvíveis, mono/multifilamentares) e técnicas"
    ]
  },
  {
    week: 46,
    area: "Cirurgia Geral",
    theme: "ATLS — Atendimento Inicial ao Politraumatizado",
    highYield: true,
    dbSubtemas: ["Atendimento Inicial ao Trauma (ATLS)", "Choque e Transfusão no Trauma"],
    details: [
      "Sistemática ABCDE do trauma e avaliação primária",
      "Via aérea definitiva: indicações (IOT, cricotireoidostomia)",
      "Choque hemorrágico: classes de hemorragia e ressuscitação",
      "Protocolo de transfusão maciça e ácido tranexâmico"
    ]
  },
  {
    week: 47,
    area: "Cirurgia Geral",
    theme: "Trauma Torácico",
    highYield: true,
    dbSubtemas: ["Trauma Torácico"],
    details: [
      "Pneumotórax hipertensivo e aberto: diagnóstico clínico e conduta imediata",
      "Hemotórax maciço e tórax instável",
      "Tamponamento cardíaco (tríade de Beck) e toracotomia de reanimação",
      "Contusão pulmonar, lesão de aorta e drenagem torácica"
    ]
  },
  {
    week: 48,
    area: "Cirurgia Geral",
    theme: "Trauma Abdominal e Choque",
    highYield: true,
    dbSubtemas: ["Trauma Abdominal", "Trauma Cranioencefálico e Raquimedular", "Trauma Cervical e Vascular", "Trauma Pélvico"],
    details: [
      "Trauma abdominal fechado vs penetrante: indicações de laparotomia",
      "FAST/e-FAST e tomografia no trauma; lavado peritoneal",
      "Manejo conservador de lesões de vísceras maciças (fígado e baço)",
      "Trauma pélvico, cirurgia de controle de danos e síndrome compartimental abdominal"
    ]
  },
  {
    week: 49,
    area: "Cirurgia Geral",
    theme: "Queimaduras",
    highYield: false,
    dbSubtemas: ["Queimaduras"],
    details: [
      "Profundidade e extensão (regra dos nove de Wallace)",
      "Fórmula de Parkland para reposição volêmica nas primeiras 24h",
      "Critérios de transferência para centro de queimados",
      "Lesão inalatória, escarotomia e cuidados com a ferida"
    ]
  },
  {
    week: 50,
    area: "Cirurgia Geral",
    theme: "Abdome Agudo Inflamatório",
    highYield: true,
    dbSubtemas: ["Apendicite Aguda", "Colecistite e Colelitíase", "Diverticulite Aguda"],
    details: [
      "Apendicite aguda: clínica, escore de Alvarado, imagem e tratamento",
      "Colecistite aguda: critérios de Tóquio e colecistectomia",
      "Diverticulite aguda: classificação de Hinchey e conduta clínica vs cirúrgica",
      "Pancreatite (visão geral) e diagnóstico diferencial do abdome agudo"
    ]
  },
  {
    week: 51,
    area: "Cirurgia Geral",
    theme: "Abdome Agudo Obstrutivo, Perfurativo e Vascular",
    highYield: false,
    dbSubtemas: ["Abdome Agudo Obstrutivo", "Abdome Agudo Perfurativo", "Isquemia Mesentérica"],
    details: [
      "Obstrução alta vs baixa (bridas, volvo, neoplasia, íleo biliar)",
      "Abdome perfurativo (pneumoperitônio, sinal de Jobert)",
      "Isquemia mesentérica aguda: dor desproporcional, acidose e angio-TC",
      "Íleo paralítico pós-operatório e síndrome de Ogilvie"
    ]
  },
  {
    week: 52,
    area: "Cirurgia Geral",
    theme: "Hérnias da Parede Abdominal",
    highYield: true,
    dbSubtemas: ["Hérnias da Parede Abdominal"],
    details: [
      "Anatomia do canal inguinal e triângulo de Hesselbach",
      "Hérnia inguinal indireta, direta e femoral (crural)",
      "Classificação de Nyhus e técnicas de correção (Lichtenstein, laparoscópica)",
      "Hérnia redutível, encarcerada e estrangulada: conduta"
    ]
  },
  {
    week: 53,
    area: "Cirurgia Geral",
    theme: "Doenças Biliares e Pancreatite Aguda",
    highYield: true,
    dbSubtemas: ["Coledocolitíase e Colangite", "Pancreatite Aguda"],
    details: [
      "Colelitíase, coledocolitíase (indicação de CPRE) e colangite (tríade de Charcot/pêntade de Reynolds)",
      "Pancreatite aguda: critérios diagnósticos e de gravidade (Ranson, Atlanta)",
      "Manejo clínico inicial (hidratação, analgesia, nutrição precoce)",
      "Complicações (pseudocisto, necrose infectada) e conduta"
    ]
  },
  {
    week: 54,
    area: "Cirurgia Geral",
    theme: "Esôfago: DRGE, Acalasia e Câncer",
    highYield: false,
    dbSubtemas: ["Doenças do Esôfago (DRGE, Acalasia, Câncer)"],
    details: [
      "DRGE: diagnóstico, complicações e esôfago de Barrett",
      "Acalasia e distúrbios motores; manometria esofágica",
      "Câncer de esôfago (escamoso vs adenocarcinoma) e fatores de risco",
      "Hérnia de hiato e divertículos esofágicos"
    ]
  },
  {
    week: 55,
    area: "Cirurgia Geral",
    theme: "Estômago: Úlcera Péptica, HDA e Câncer Gástrico",
    highYield: true,
    dbSubtemas: ["Estômago (Úlcera, HDA, Câncer Gástrico)", "Cirurgia Bariátrica"],
    details: [
      "Doença ulcerosa péptica, H. pylori e complicações (perfuração, obstrução)",
      "Hemorragia digestiva alta: classificação de Forrest e abordagem endoscópica",
      "Câncer gástrico: fatores de risco, tipos e estadiamento",
      "Cirurgia bariátrica: indicações e principais técnicas"
    ]
  },
  {
    week: 56,
    area: "Cirurgia Geral",
    theme: "Cólon, Reto e Ânus",
    highYield: true,
    dbSubtemas: ["Câncer Colorretal", "Doenças Orificiais (Hemorroida, Fissura, Fístula)"],
    details: [
      "Câncer colorretal: rastreamento, fatores de risco e estadiamento",
      "Doença diverticular dos cólons e suas complicações",
      "Doença inflamatória intestinal (Crohn vs retocolite) — visão cirúrgica",
      "Doenças orificiais: hemorroidas, fissura anal, fístula e abscesso perianal"
    ]
  },
  {
    week: 57,
    area: "Cirurgia Geral",
    theme: "Cirurgia Vascular",
    highYield: false,
    dbSubtemas: ["Cirurgia Vascular (Aneurisma, Isquemia Arterial, Varizes)"],
    details: [
      "Aneurisma de aorta abdominal: rastreamento e indicação de correção",
      "Isquemia arterial aguda (5 P) e crônica (claudicação intermitente)",
      "Doença venosa: varizes, insuficiência venosa e trombose venosa profunda",
      "Pé diabético e úlceras vasculares"
    ]
  },
  {
    week: 58,
    area: "Cirurgia Geral",
    theme: "Tireoide, Paratireoide e Cabeça e Pescoço",
    highYield: false,
    dbSubtemas: ["Tireoide e Paratireoide"],
    details: [
      "Nódulo de tireoide: investigação (PAAF, classificação de Bethesda)",
      "Câncer de tireoide (papilífero, folicular, medular) e conduta",
      "Hiperparatireoidismo e manejo cirúrgico",
      "Massas cervicais e princípios do câncer de cabeça e pescoço"
    ]
  },

  // ═══════════════ CLÍNICA MÉDICA ═══════════════
  {
    week: 59,
    area: "Clínica Médica",
    theme: "Hipertensão Arterial Sistêmica",
    highYield: true,
    dbSubtemas: ["Hipertensão Arterial Sistêmica"],
    details: [
      "Diagnóstico e estratificação de risco cardiovascular",
      "Tratamento não medicamentoso e classes de primeira linha (IECA, BRA, BCC, tiazídicos)",
      "Hipertensão resistente e secundária (renovascular, hiperaldosteronismo, feocromocitoma)",
      "Urgência vs emergência hipertensiva e lesão de órgão-alvo"
    ]
  },
  {
    week: 60,
    area: "Clínica Médica",
    theme: "Dislipidemia e Prevenção Cardiovascular",
    highYield: false,
    dbSubtemas: ["Dislipidemia e Risco Cardiovascular"],
    details: [
      "Metas de LDL conforme risco cardiovascular",
      "Estatinas, ezetimiba e inibidores de PCSK9",
      "Hipertrigliceridemia e risco de pancreatite",
      "Estratificação de risco (escores) e prevenção primária vs secundária"
    ]
  },
  {
    week: 61,
    area: "Clínica Médica",
    theme: "Diabetes Mellitus e Complicações Agudas",
    highYield: true,
    dbSubtemas: ["Diabetes Mellitus e Complicações Agudas"],
    details: [
      "Critérios diagnósticos (glicemia, TOTG, HbA1c) e pré-diabetes",
      "Tratamento do DM2 (metformina, iSGLT2, análogos de GLP-1, sulfonilureias)",
      "Insulinoterapia no DM1 (basal-bolus)",
      "Cetoacidose diabética e estado hiperosmolar: manejo de insulina, volume e potássio"
    ]
  },
  {
    week: 62,
    area: "Clínica Médica",
    theme: "Tireoidopatias e Distúrbios da Adrenal",
    highYield: false,
    dbSubtemas: ["Tireoidopatias", "Distúrbios da Adrenal e Hipófise"],
    details: [
      "Hipotireoidismo e hipertireoidismo (Graves, bócio, tireoidites)",
      "Crise tireotóxica e coma mixedematoso",
      "Insuficiência adrenal e crise addisoniana; síndrome de Cushing",
      "Interpretação de TSH, T4 livre e autoanticorpos"
    ]
  },
  {
    week: 63,
    area: "Clínica Médica",
    theme: "Síndromes Coronarianas Agudas",
    highYield: true,
    dbSubtemas: ["Síndromes Coronarianas Agudas"],
    details: [
      "IAM com supra de ST: ECG por parede e indicação de reperfusão (trombólise vs angioplastia)",
      "SCA sem supra e angina instável: estratificação (GRACE/TIMI)",
      "Dupla antiagregação, anticoagulação e terapia adjuvante",
      "Complicações mecânicas e elétricas do infarto"
    ]
  },
  {
    week: 64,
    area: "Clínica Médica",
    theme: "Insuficiência Cardíaca",
    highYield: true,
    dbSubtemas: ["Insuficiência Cardíaca"],
    details: [
      "Diagnóstico (critérios de Framingham) e classificação por fração de ejeção",
      "Terapia que reduz mortalidade na ICFEr (IECA/BRA/ARNI, betabloqueador, antagonista de aldosterona, iSGLT2)",
      "IC aguda: perfis hemodinâmicos e tratamento no pronto-socorro",
      "Dispositivos, ressincronização e manejo das descompensações"
    ]
  },
  {
    week: 65,
    area: "Clínica Médica",
    theme: "Arritmias e Fibrilação Atrial",
    highYield: false,
    dbSubtemas: ["Arritmias e Fibrilação Atrial"],
    details: [
      "Fibrilação atrial: controle de ritmo vs frequência e anticoagulação (CHA2DS2-VASc, HAS-BLED)",
      "Taquiarritmias de QRS estreito e largo: conduta na instabilidade vs estabilidade",
      "Bradiarritmias e bloqueios atrioventriculares; indicação de marca-passo",
      "Parada cardiorrespiratória: ritmos chocáveis e não chocáveis"
    ]
  },
  {
    week: 66,
    area: "Clínica Médica",
    theme: "Asma e DPOC",
    highYield: true,
    dbSubtemas: ["Asma e DPOC"],
    details: [
      "Diagnóstico diferencial pela espirometria (reversibilidade)",
      "Tratamento de manutenção da asma (GINA) e da crise",
      "Tratamento do DPOC (GOLD) e exacerbação (antibiótico, corticoide, VNI)",
      "Oxigenoterapia domiciliar prolongada: critérios e benefício"
    ]
  },
  {
    week: 67,
    area: "Clínica Médica",
    theme: "Tromboembolismo Venoso, TEP e Derrame Pleural",
    highYield: true,
    dbSubtemas: ["Tromboembolismo Venoso e TEP", "Derrame Pleural e Doenças Pleurais"],
    details: [
      "TVP e TEP: escores de probabilidade (Wells), D-dímero e angio-TC",
      "Estratificação de gravidade do TEP e indicação de trombólise",
      "Anticoagulação (heparinas, DOACs) e tempo de tratamento",
      "Derrame pleural: critérios de Light (transudato vs exsudato) e toracocentese"
    ]
  },
  {
    week: 68,
    area: "Clínica Médica",
    theme: "Pneumonia, Tuberculose e Infecções Respiratórias",
    highYield: true,
    dbSubtemas: ["Pneumonia e Infecções Respiratórias", "Tuberculose"],
    details: [
      "Pneumonia adquirida na comunidade: CURB-65, local de tratamento e antibiótico empírico",
      "Pneumonia hospitalar e associada à ventilação",
      "Tuberculose: diagnóstico, esquema RIPE e tratamento da ILTB",
      "Micoses pulmonares e abscesso pulmonar"
    ]
  },
  {
    week: 69,
    area: "Clínica Médica",
    theme: "Nefrologia: IRA e Doença Renal Crônica",
    highYield: true,
    dbSubtemas: ["Injúria Renal Aguda", "Doença Renal Crônica"],
    details: [
      "Lesão renal aguda: classificação KDIGO e diferenciação pré-renal/renal/pós-renal",
      "Doença renal crônica: estadiamento (TFG e albuminúria) e complicações",
      "Distúrbio mineral e ósseo, anemia da DRC",
      "Indicações de diálise de urgência (hipercalemia, acidose, volemia, uremia)"
    ]
  },
  {
    week: 70,
    area: "Clínica Médica",
    theme: "Distúrbios Hidroeletrolíticos e Ácido-Básicos",
    highYield: true,
    dbSubtemas: ["Distúrbios Hidroeletrolíticos e Ácido-Base"],
    details: [
      "Hiponatremia (por volemia e osmolaridade) e risco de mielinólise por correção rápida",
      "Hipernatremia e distúrbios do potássio (ECG e estabilização de membrana)",
      "Acidose metabólica: ânion gap e diagnóstico diferencial",
      "Interpretação da gasometria (distúrbios respiratórios e compensações)"
    ]
  },
  {
    week: 71,
    area: "Clínica Médica",
    theme: "Gastroenterologia: DRGE, Úlcera e DII",
    highYield: false,
    dbSubtemas: ["Doenças do Esôfago e Estômago", "Doença Inflamatória Intestinal e Diarreia Crônica"],
    details: [
      "Dispepsia, DRGE e H. pylori: diagnóstico e tratamento",
      "Doença inflamatória intestinal (Crohn vs retocolite ulcerativa)",
      "Diarreia crônica, síndromes disabsortivas e doença celíaca",
      "Síndrome do intestino irritável e hemorragia digestiva baixa"
    ]
  },
  {
    week: 72,
    area: "Clínica Médica",
    theme: "Hepatologia: Hepatites, Cirrose e Complicações",
    highYield: true,
    dbSubtemas: ["Hepatites Virais", "Cirrose e Complicações"],
    details: [
      "Hepatites virais A, B, C, D e E: sorologias e história natural",
      "Cirrose e suas complicações (ascite, PBE, encefalopatia, síndrome hepatorrenal)",
      "Hemorragia por varizes esofágicas: profilaxia e tratamento",
      "Insuficiência hepática aguda e rastreamento de carcinoma hepatocelular"
    ]
  },
  {
    week: 73,
    area: "Clínica Médica",
    theme: "Hematologia: Anemias, Neoplasias e Coagulação",
    highYield: false,
    dbSubtemas: ["Anemias", "Leucemias e Linfomas", "Distúrbios da Coagulação e Plaquetas"],
    details: [
      "Investigação das anemias (micro, normo e macrocíticas); ferropriva, doença crônica e megaloblástica",
      "Anemias hemolíticas e falciforme",
      "Leucemias e linfomas: apresentação e diagnóstico inicial",
      "Distúrbios da hemostasia, plaquetopenias (PTI) e coagulopatias"
    ]
  },
  {
    week: 74,
    area: "Clínica Médica",
    theme: "Reumatologia: AR, LES, Gota e Vasculites",
    highYield: false,
    dbSubtemas: ["Artrites e Doenças Reumatológicas (AR, Gota, Osteoartrite)", "Lúpus e Doenças Autoimunes Sistêmicas"],
    details: [
      "Artrite reumatoide: critérios, autoanticorpos e tratamento",
      "Lúpus eritematoso sistêmico: critérios diagnósticos e nefrite lúpica",
      "Gota e artrites por cristais; abordagem da monoartrite aguda",
      "Espondiloartrites e vasculites sistêmicas"
    ]
  },
  {
    week: 75,
    area: "Clínica Médica",
    theme: "Neurologia: AVC, Cefaleias, Epilepsia e Demências",
    highYield: true,
    dbSubtemas: ["AVC e Doenças Cerebrovasculares", "Cefaleias", "Epilepsia e Doenças Neuromusculares", "Demências e Parkinson"],
    details: [
      "AVC isquêmico: janela de trombólise e trombectomia; AVC hemorrágico e HSA",
      "Cefaleias primárias (enxaqueca, tensional, em salvas) e sinais de alarme",
      "Epilepsia e estado de mal epiléptico",
      "Demências (Alzheimer, vascular) e síndromes parkinsonianas"
    ]
  },
  {
    week: 76,
    area: "Clínica Médica",
    theme: "Infectologia: HIV, Arboviroses e Endocardite",
    highYield: true,
    dbSubtemas: ["HIV/AIDS e Infecções Oportunistas", "Arboviroses e Doenças Infecciosas Tropicais", "Endocardite Infecciosa"],
    details: [
      "HIV/AIDS: diagnóstico, TARV, infecções oportunistas e profilaxias",
      "Dengue, zika e chikungunya: classificação de risco e manejo",
      "Endocardite infecciosa (critérios de Duke) e sepse/choque séptico (bundle da 1ª hora)",
      "Meningites, ITU/pielonefrite, celulite e leptospirose"
    ]
  },
  {
    week: 77,
    area: "Clínica Médica",
    theme: "Emergências Clínicas e Toxicologia",
    highYield: true,
    dbSubtemas: ["Sepse e Choque", "Emergências Clínicas e Intoxicações"],
    details: [
      "Parada cardiorrespiratória e ACLS; cuidados pós-parada",
      "Choque (hipovolêmico, cardiogênico, distributivo, obstrutivo) e anafilaxia",
      "Intoxicações comuns e antídotos; distúrbios do nível de consciência",
      "Abordagem do paciente grave e sinais de deterioração"
    ]
  },
  {
    week: 78,
    area: "Clínica Médica",
    theme: "Psiquiatria: Depressão, Ansiedade e Emergências",
    highYield: false,
    dbSubtemas: ["Transtornos Psiquiátricos"],
    details: [
      "Transtornos depressivos e de ansiedade: diagnóstico e tratamento",
      "Transtorno bipolar e espectro da esquizofrenia",
      "Emergências psiquiátricas: risco de suicídio, agitação e síndromes por substâncias",
      "Delirium vs demência; síndrome serotoninérgica e neuroléptica maligna"
    ]
  },
  {
    week: 79,
    area: "Clínica Médica",
    theme: "Geriatria e Cuidados Paliativos",
    highYield: false,
    dbSubtemas: [],
    details: [
      "Grandes síndromes geriátricas (quedas, imobilidade, incontinência, delirium)",
      "Avaliação geriátrica ampla e polifarmácia (critérios de Beers)",
      "Cuidados paliativos: controle de sintomas e comunicação de más notícias",
      "Terminalidade, ortotanásia e manejo da dor"
    ]
  },
  {
    week: 80,
    area: "Clínica Médica",
    theme: "Reta Final: Revisão Integrada e Simulados",
    highYield: true,
    dbSubtemas: [],
    details: [
      "Revisão dos temas de alto rendimento das 5 áreas",
      "Resolução de provas anteriores da USP (HC-FMUSP e HCRP) cronometradas",
      "Foco nas suas áreas e subtemas mais fracos (ver Análise de Desempenho)",
      "Simulados completos e ajuste fino da estratégia de prova"
    ]
  }
];
