import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("""
    SELECT id, subtema, topic, stem 
    FROM questions 
    WHERE area LIKE '%Preventiva%'
""").fetchall()

def classify_prev_question(subtema, topic, stem):
    text = (str(topic) + " " + str(stem)).lower()
    
    # 1. Ética e Bioética
    if any(re.search(p, text) for p in [r"ética médica", r"bioética", r"código de ética", r"sigilo profissional", r"segredo médico", r"autonomia", r"beneficência", r"não maleficência", r"justiça", r"atestado médico", r"declaração de óbito", r"prontuário", r"erro médico", r"consentimento informado", r"termo de consentimento"]):
        return "Ética médica, Bioética e Documentação"

    # 2. Testes Diagnósticos
    if any(re.search(p, text) for p in [r"sensibilidade", r"especificidade", r"valor preditivo positivo", r"\bvpp\b", r"valor preditivo negativo", r"\bvpn\b", r"razão de verossimilhança", r"curva roc", r"ponto de corte", r"acurácia", r"teste diagnóstico", r"teste em paralelo", r"teste em série"]):
        return "Estatística de Testes Diagnósticos"

    # 3. Estudos Epidemiológicos - Análise Estatística vs Classificação
    if any(re.search(p, text) for p in [r"risco relativo", r"\brr\b", r"odds ratio", r"\bor\b", r"razão de chances", r"razão de prevalência", r"risco atribuível", r"redução do risco", r"redução absoluta", r"\brrr\b", r"\brar\b", r"\bnnt\b", r"\bnnh\b", r"teste de hipótese", r"erro tipo i", r"erro tipo ii", r"valor de p", r"intervalo de confiança", r"viés", r"fator de confusão"]):
        return "Estudos Epidemiológicos (Análise Estatística e Aplicação)"
    if any(re.search(p, text) for p in [r"estudo de coorte", r"caso-controle", r"ensaio clínico", r"estudo transversal", r"estudo ecológico", r"meta-análise", r"revisão sistemática", r"delineamento de estudo", r"randomização", r"mascaramento", r"duplo-cego"]):
        return "Estudos Epidemiológicos (Classificação)"

    # 4. Demografia e Indicadores
    if any(re.search(p, text) for p in [r"transição demográfica", r"taxa de fecundidade", r"pirâmide etária", r"envelhecimento populacional", r"esperança de vida", r"razão de dependência"]):
        return "Perfis e Indicadores demográficos"
    if any(re.search(p, text) for p in [r"taxa de mortalidade", r"coeficiente de mortalidade", r"mortalidade infantil", r"mortalidade materna", r"letalidade", r"incidência", r"prevalência", r"padronização de taxas", r"daly", r"anos potenciais de vida perdidos"]):
        return "Indicadores de Morbimortalidade"

    # 5. Prevenção
    if any(re.search(p, text) for p in [r"prevenção primária", r"prevenção secundária", r"prevenção terciária", r"prevenção quaternária", r"prevenção primordial", r"rastreamento", r"screening", r"sobrediagnóstico", r"sobreatendimento", r"iatrogenia"]):
        return "Níveis de Prevenção"

    # 6. Vigilância em Saúde do Trabalhador
    if any(re.search(p, text) for p in [r"saúde do trabalhador", r"doença ocupacional", r"acidente de trabalho", r"\bcat\b", r"comunicação de acidente", r"ler/dort", r"perda auditiva induzida", r"pneumoconiose", r"silicose", r"asbestose", r"benzenismo", r"saturnismo"]):
        return "Vigilância em Saúde do Trabalhador"

    # 7. Epidemias e Notificação
    if any(re.search(p, text) for p in [r"notificação compulsória", r"sinan", r"lista nacional de notificação", r"notificação imediata", r"ficha de notificação", r"bloqueio vacinal"]):
        return "Notificação"
    if any(re.search(p, text) for p in [r"epidemia", r"endemia", r"pandemia", r"surto", r"curva epidêmica", r"número reprodutivo básico", r"\br0\b", r"imunidade de rebanho", r"vigilância epidemiológica", r"canal endêmico"]):
        return "Epidemias, Endemias e Pandemias"

    # 8. SUS - História, Evolução, APS
    if any(re.search(p, text) for p in [r"atenção primária", r"\baps\b", r"estratégia saúde da família", r"\besf\b", r"starfield", r"longitudinalidade", r"coordenação do cuidado", r"primeiro contato", r"integralidade da aps", r"método clínico centrado", r"genograma", r"ecomapa", r"pts"]):
        return "Atenção Primária à Saúde"
    if any(re.search(p, text) for p in [r"inamps", r"caixas de aposentadoria", r"caps", r"iaps", r"reforma sanitária", r"8ª conferência", r"movimento sanitário", r"modelo sanitarista-campanhista", r"constituição de 1988"]):
        return "Aspectos Históricos do SUS"
    if any(re.search(p, text) for p in [r"lei 8080", r"lei 8142", r"nob-sus", r"noas-sus", r"pacto pela saúde", r"decreto 7508", r"financiamento do sus", r"controle social", r"conselho de saúde", r"conferência de saúde", r"princípios do sus", r"descentralização", r"regionalização", r"hierarquização", r"participação popular", r"universalidade", r"equidade", r"integralidade"]):
        return "A Evolução do SUS"

    # Fallback
    sub = str(subtema)
    if "Ética" in sub: return "Ética médica, Bioética e Documentação"
    if "Bioestatística" in sub: return "Estatística de Testes Diagnósticos"
    if "Delineamentos" in sub: return "Estudos Epidemiológicos (Classificação)"
    if "Transição" in sub: return "Perfis e Indicadores demográficos"
    if "Níveis" in sub: return "Níveis de Prevenção"
    if "Ocupacional" in sub: return "Vigilância em Saúde do Trabalhador"
    if "Vigilância" in sub: return "Epidemias, Endemias e Pandemias"
    if "História" in sub: return "Aspectos Históricos do SUS"
    if "Legislação" in sub or "Redes" in sub: return "A Evolução do SUS"
    if "Princípios" in sub: return "Atenção Primária à Saúde"
    
    return "Atenção Primária à Saúde"

updates = []
for q in questions:
    new_sub = classify_prev_question(q["subtema"], q["topic"], q["stem"])
    updates.append((new_sub, q["id"]))

print(f"Applying {len(updates)} subtema updates to medquest.db for Preventiva...")
conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", updates)
conn.commit()
print("All Preventiva questions updated in local medquest.db!")
