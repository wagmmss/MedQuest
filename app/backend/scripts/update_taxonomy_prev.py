import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

with open("preventiva_plan_compiled.json", "r", encoding="utf-8") as f:
    prev_plan = json.load(f)

# Built detailed pedagogical curriculum descriptions for the 13 Medway Preventiva modules
prev_module_details = {
    "Ética médica, Bioética e Documentação": [
        "Princípios fundamentais da Bioética principialista: Autonomia, Beneficência, Não Maleficência e Justiça",
        "Código de Ética Médica (CEM): sigilo profissional, quebra justificada de sigilo e responsabilidade profissional",
        "Documentos médicos: elaboração correta de Atestados Médicos, Prontuário Médico e Notificação",
        "Declaração de Óbito (DO): regras de preenchimento (causa básica, imediata e contribuintes) e competência para emissão (SVO vs IML vs médico assistente)"
    ],
    "Estudos Epidemiológicos (Análise Estatística e Aplicação)": [
        "Medidas de associação epidemiológica: Risco Relativo (RR), Odds Ratio (OR), Razão de Prevalências (RP)",
        "Medidas de impacto: Risco Atribuível (RA), Redução Absoluta do Risco (RAR), Redução Relativa do Risco (RRR)",
        "Número Necessário para Tratar (NNT) e Número Necessário para Causar Dano (NNH)",
        "Inferência estatística, testes de hipótese (erro tipo I / alfa, erro tipo II / beta, valor de p) e intervalos de confiança de 95%"
    ],
    "Estudos Epidemiológicos (Classificação)": [
        "Classificação dos estudos epidemiológicos: observacionais vs intervencionais / experimentais",
        "Estudo de Coorte: desenho prospectivo/retrospectivo, cálculo de incidência e viéses comuns",
        "Estudo Caso-Controle: desenho retrospectivo, seleção de controles, pareamento e cálculo de Odds Ratio",
        "Ensaio Clínico Randomizado: randomização, mascaramento (duplo-cego), intenção de tratar e fases da pesquisa clínica"
    ],
    "Indicadores de Morbimortalidade": [
        "Conceitos fundamentais de Morbidade: Incidência (casos novos) vs Prevalência (casos existentes) e fatores determinantes",
        "Coeficiente de Mortalidade Geral e Coeficientes Específicos (Mortalidade Infantil, Neonatal Precoce/Tardia, Pós-neonatal)",
        "Mortalidade Materna e Razão de Mortalidade Materna (RMM)",
        "Letalidade vs Mortalidade, Curvas de Nelson Moraes e Anos Potenciais de Vida Perdidos (APVP / DALY)"
    ],
    "Perfis e Indicadores demográficos": [
        "Transição demográfica no Brasil: fases da transição, queda da fecundidade e mortalidade",
        "Transição epidemiológica: tripla carga de doenças (infecciosas, crônico-degenerativas e causas externas)",
        "Estrutura etária da população brasileira e leitura de pirâmides etárias",
        "Índice de Envelhecimento, Razão de Dependência e Esperança de Vida ao Nascer"
    ],
    "Níveis de Prevenção": [
        "História Natural da Doença (Leavell & Clark): períodos pré-patogênico e patogênico",
        "Prevenção Primordial, Primária (promoção da saúde e proteção específica) e Secundária (diagnóstico precoce e tratamento imediato)",
        "Prevenção Terciária (reabilitação e limitação da incapacidade)",
        "Prevenção Quaternária: conceito de iatrogenia médica, sobrediagnóstico (overdiagnosis), sobretratamento (overtreatment) e desprescrição"
    ],
    "Aspectos Históricos do SUS": [
        "História da saúde pública e previdência social no Brasil: Caixas de Aposentadoria e Pensões (CAPs - Lei Eloy Chaves de 1923)",
        "Institutos de Aposentadorias e Pensões (IAPs) na era Vargas e fusão no INPS/INAMPS",
        "Movimento da Reforma Sanitária Brasileira, Centro Brasileiro de Estudos de Saúde (CEBES) e 8ª Conferência Nacional de Saúde (1986)",
        "Criação do Sistema Único de Saúde (SUS) na Constituição Federal de 1988 (Artigos 196 a 200)"
    ],
    "A Evolução do SUS": [
        "Legislação estruturante do SUS: Lei Orgânica da Saúde 8.080/1990 (princípios doutrinários e organizacionais) e Lei 8.142/1990 (participação popular e repasses)",
        "Controle Social no SUS: Conselhos de Saúde e Conferências de Saúde (composição paritária 50% usuários)",
        "Evolução normativa: Normas Operacionais Básicas (NOB 91, 93, 96), NOAS 2001/2002, Pacto pela Saúde (2006) e Decreto Presidencial 7.508/2011",
        "Financiamento do SUS: Emendas Constitucionais (EC 29/2000, EC 95/2016), blocos de financiamento e desregulamentação recente"
    ],
    "Atenção Primária à Saúde": [
        "Fundamentos e atributos da Atenção Primária à Saúde segundo Barbara Starfield (Essenciais: Acesso/Primeiro Contato, Longitudinalidade, Integralidade, Coordenação; Derivados: Orientação Familiar, Comunitária, Competência Cultural)",
        "Estratégia Saúde da Família (ESF) e Política Nacional de Atenção Básica (PNAB)",
        "Instrumentos de abordagem familiar: Genograma (árvore genealógica familiar de 3 gerações), Ecomapa, FIRO e Ciclo de Vida Familiar",
        "Método Clínico Centrado na Pessoa (MCCP): os 4 componentes práticos no atendimento clínico"
    ],
    "Estatística de Testes Diagnósticos": [
        "Propriedades intrínsecas dos testes: Sensibilidade (capacidade de detectar doentes) e Especificidade (capacidade de detectar sadios)",
        "Propriedades extrínsecas dependentes da prevalência: Valor Preditivo Positivo (VPP) e Valor Preditivo Negativo (VPN)",
        "Razão de Verossimilhança Positiva (RV+) e Negativa (RV-): cálculo e interpretação no nomograma de Fagan",
        "Curva ROC (Receiver Operating Characteristic): área sob a curva (AUC), sensibilidade vs 1-especificidade e definição de ponto de corte"
    ],
    "Epidemias, Endemias e Pandemias": [
        "Conceitos ecológicos de Endemia, Epidemia, Pandemia e Surto",
        "Curva epidêmica: interpretação de epidemias por fonte comum pontual/contínua vs propagada",
        "Diagrama de controle / Canal endêmico (quartis superior, mediano e inferior) e identificação de epidemia",
        "Número Reprodutivo Básico (R0), Número Reprodutivo Efetivo (Rt) e cálculo do limiar de imunidade de rebanho"
    ],
    "Notificação": [
        "Sistema de Informação de Agravos de Notificação (SINAN) e Portaria de Consolidação da Lista Nacional de Notificação Compulsória",
        "Periodicidade da notificação: Notificação Imediata (até 24 horas para MS/Estado/Município) vs Notificação Semanal",
        "Doenças, agravos e eventos de saúde pública de notificação compulsória",
        "Fluxo da notificação, notificação negativa e investigação epidemiológica de contatos e bloqueio"
    ],
    "Vigilância em Saúde do Trabalhador": [
        "Princípios da Saúde do Trabalhador e classificação de Schilling para doenças relacionadas ao trabalho (Grupos I, II e III)",
        "Comunicação de Acidente de Trabalho (CAT): emissão obrigatória para acidentes típicos, de trajeto e doenças profissionais",
        "Principais agravos ocupacionais: LER/DORT, Perda Auditiva Induzida por Ruído (PAIR)",
        "Pneumoconioses (Silicose, Asbestose), Intoxicações por metais pesados (Chumbo/Saturnismo, Mercúrio/Hidrargirismo, Benzenismo) e Acidentes com material biológico"
    ]
}

new_prev_macro = []
for item in prev_plan:
    name = item["name"]
    high_yield = item["high_yield"]
    details = prev_module_details.get(name, [name])
    
    new_prev_macro.append({
        "theme": name,
        "highYield": high_yield,
        "dbSubtemas": [name],
        "details": details
    })

# Find Preventiva area in taxonomy
prev_index = -1
for i, area_data in enumerate(taxonomy):
    area_name = area_data.get("area", "")
    if "Preventiva" in area_name:
        prev_index = i
        break

if prev_index >= 0:
    taxonomy[prev_index]["macroThemes"] = new_prev_macro
    print(f"Replaced Preventiva with {len(new_prev_macro)} Medway macro-themes!")
else:
    taxonomy.append({
        "area": "Preventiva",
        "macroThemes": new_prev_macro
    })
    print("Added Preventiva to taxonomy!")

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(taxonomy, f, ensure_ascii=False, indent=2)

print("Saved updated taxonomy.json for Preventiva!")
