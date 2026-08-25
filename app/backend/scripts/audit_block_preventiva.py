"""
Auditoria e reclassificação de alta precisão do Bloco 1: Medicina Preventiva
Analisa as questões de Preventiva com contexto clínico integral e classifica nos 13 subtemas canônicos.
"""

import sqlite3
import json
import re
import unicodedata
import sys

sys.stdout.reconfigure(encoding="utf-8")

def norm(text):
    text = unicodedata.normalize('NFD', str(text or ''))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def match_any(text, patterns):
    for p in patterns:
        if re.search(r'\b' + re.escape(p) + r'\b', text):
            return True
    return False

CANONICAL_THEMES = [
    "Ética Médica, Bioética e Prontuários / Documentos",
    "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística",
    "Delineamentos e Classificação dos Estudos Epidemiológicos",
    "Indicadores de Saúde e Coeficientes de Morbimortalidade",
    "Transição Demográfica e Perfis Populacionais",
    "História Natural da Doença e Níveis de Prevenção",
    "História das Políticas de Saúde e Origens do SUS",
    "Legislação, Diretrizes e Evolução do SUS",
    "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)",
    "Avaliação de Testes Diagnósticos e Curva ROC",
    "Vigilância Epidemiológica: Endemias, Epidemias e Surtos",
    "Vigilância em Saúde e Notificação Compulsória (SINAN)",
    "Saúde do Trabalhador e Doenças Ocupacionais"
]

def classify_preventiva_question(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    full_text = f"{stem} {alts} {exp} {topic} {subtema_orig}"
    full_norm = norm(full_text)
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    
    # 1. Ética Médica, Bioética, Sigilo, Declaração de Óbito, Atestados
    if match_any(full_norm, [
        'declaracao de obito', 'declaracoes de obito', 'atestado de obito', 'atestados de obito', 
        'preenchimento da declaracao de obito', 'causa basica da morte', 'causa terminal', 'causa intermediaria',
        'sigilo medico', 'segredo medico', 'quebra de sigilo', 'termo de consentimento livre e esclarecido', 'tcle',
        'consentimento informado', 'autonomia', 'beneficencia', 'nao maleficencia', 'justica distributiva', 
        'diretivas antecipadas de vontade', 'testamento vital', 'codigo de etica medica', 'cem', 'responsabilidade etica', 
        'conselho regional de medicina', 'conselho federal de medicina', 'crm', 'cfm', 'comissao de etica medica', 
        'iatrogenia', 'impericia', 'imprudencia', 'negligencia', 'prontuario medico', 'guarda do prontuario', 
        'obito fetal', 'necropsia', 'servico de verificacao de obito', 'svo', 'instituto medico legal', 'iml', 
        'morte suspeita', 'morte violenta', 'morte natural', 'declaracao de nascimento', 'erro medico', 
        'distanasia', 'ortotanasia', 'eutanasia', 'cuidados paliativos e etica'
    ]) or (match_any(topic_norm, ['etica', 'bioetica', 'obito', 'atestado', 'sigilo', 'prontuario']) and not match_any(stem_norm, ['coeficiente de mortalidade', 'taxa de mortalidade'])):
        return "Ética Médica, Bioética e Prontuários / Documentos", 1.0, "Questão sobre ética médica, bioética, sigilo profissional, prontuários ou preenchimento de declaração/atestado de óbito."

    # 2. Avaliação de Testes Diagnósticos e Curva ROC
    if match_any(full_norm, [
        'sensibilidade', 'especificidade', 'valor preditivo positivo', 'valor preditivo negativo', 'vpp', 'vpn',
        'curva roc', 'area sob a curva roc', 'razao de verossimilhanca', 'likelihood ratio', 'acuracia',
        'ponto de corte', 'falso positivo', 'falso negativo', 'verdadeiro positivo', 'verdadeiro negativo',
        'testes em paralelo', 'testes em serie', 'teste de triagem', 'teste confirmatorio', 'kappa',
        'coeficiente kappa', 'concordancia interobservador', 'tabela 2x2', 'padrao-ouro', 'padrao ouro'
    ]) and not match_any(full_norm, ['ensaios clinicos', 'estudo de coorte', 'caso-controle']):
        return "Avaliação de Testes Diagnósticos e Curva ROC", 1.0, "Questão sobre avaliação de testes diagnósticos, sensibilidade, especificidade, valores preditivos e curva ROC."

    # 3. Estudos Epidemiológicos: Medidas de Associação e Análise Estatística
    if match_any(full_norm, [
        'risco relativo', 'razao de chances', 'odds ratio', 'risco atribuivel', 'reducao absoluta do risco',
        'reducao relativa do risco', 'numero necessario para tratar', 'nnt', 'numero necessario para causar dano',
        'nnh', 'intervalo de confianca', 'valor p', 'erro tipo i', 'erro tipo ii', 'erro alfa', 'erro beta',
        'poder estatistico', 'teste t de student', 'qui-quadrado', 'qui quadrado', 'regressao linear', 'regressao logistica',
        'fator de confusao', 'confundimento', 'vies de selecao', 'vies de afericao', 'vies de memoria', 'vies de informacao',
        'modificacao de efeito', 'analise por intencao de tratar', 'incidencia acumulada', 'densidade de incidencia'
    ]) and not match_any(topic_norm, ['delineamentos', 'desenhos']):
        return "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística", 1.0, "Questão sobre medidas de associação epidemiológica (RR, OR, NNT), testes estatísticos, erros ou vieses."

    # 4. Delineamentos e Classificação dos Estudos Epidemiológicos
    if match_any(full_norm, [
        'estudo de coorte', 'estudo de caso-controle', 'estudo de caso controle', 'ensaio clinico randomizado',
        'ensaio clinico controlado', 'estudo transversal', 'estudo seccional', 'estudo ecologico', 'falacia ecologica',
        'revisao sistematica', 'meta-analise', 'metanalise', 'duplo-cego', 'duplo cego', 'placebo',
        'fase i', 'fase ii', 'fase iii', 'fase iv', 'longitudinal', 'agregado', 'individual', 'observacional',
        'experimental', 'quase-experimental', 'delineamento do estudo', 'tipo de estudo', 'desenho do estudo',
        'ensaio comunitário', 'estudo de intervencao'
    ]) or match_any(topic_norm, ['delineamento', 'tipo de estudo', 'estudos epidemiologicos']):
        return "Delineamentos e Classificação dos Estudos Epidemiológicos", 1.0, "Questão sobre desenho, delineamento e classificação metodológica de estudos epidemiológicos."

    # 5. Indicadores de Saúde e Coeficientes de Morbimortalidade
    if match_any(full_norm, [
        'coeficiente de mortalidade', 'taxa de mortalidade infantil', 'taxa de mortalidade materna',
        'mortalidade neonatal precoce', 'mortalidade neonatal tardia', 'mortalidade pos-neonatal',
        'mortalidade perinatal', 'indice de swaroop-uemura', 'curva de nelson moraes', 'mortalidade proporcional',
        'anos potenciais de vida perdidos', 'apvp', 'daly', 'qaly', 'taxa de letalidade', 'coeficiente de letalidade',
        'coeficiente de natalidade', 'razao de mortalidade materna', 'indicadores de saude', 'indicadores demograficos',
        'padronizacao de taxas', 'padronizacao direta', 'padronizacao indireta'
    ]) or match_any(topic_norm, ['indicadores', 'coeficientes', 'morbimortalidade']):
        return "Indicadores de Saúde e Coeficientes de Morbimortalidade", 1.0, "Questão sobre indicadores epidemiológicos de saúde e coeficientes de morbimortalidade."

    # 6. Transição Demográfica e Perfis Populacionais
    if match_any(full_norm, [
        'transicao demografica', 'transicao epidemiologica', 'piramide etaria', 'envelhecimento populacional',
        'taxa de fecundidade', 'taxa de natalidade', 'razao de dependencia', 'indice de envelhecimento',
        'dupla carga de doencas', 'tripla carga de doencas', 'esperanca de vida ao nascer', 'expectativa de vida',
        'bonus demografico', 'janela de oportunidade demografica'
    ]) or match_any(topic_norm, ['transicao', 'demografia']):
        return "Transição Demográfica e Perfis Populacionais", 1.0, "Questão sobre dinâmica populacional, pirâmides etárias e transições demográfica e epidemiológica."

    # 7. Saúde do Trabalhador e Doenças Ocupacionais
    if match_any(full_norm, [
        'saude do trabalhador', 'doenca ocupacional', 'doenca profissional', 'acidente de trabalho',
        'comunicacao de acidente de trabalho', 'cat', 'nexo tecnico epidemiologico', 'netep',
        'perda auditiva induzida por ruido', 'pair', 'ler/dort', 'ler-dort', 'tenossinovite ocupacional',
        'silicose', 'asbestose', 'pneumoconiose', 'saturnismo', 'intoxicacao por chumbo ocupacional',
        'intoxicacao por mercurio', 'hidrargirismo', 'intoxicacao por benzeno', 'benzenismo', 'asbesto',
        'amianto', 'mesotelioma ocupacional', 'nr-32', 'nr 32', 'norma regulamentadora', 'burnout ocupacional',
        'cerest', 'centro de referencia em saude do trabalhador', 'inss', 'auxilio-doenca acidentario',
        'medicina do trabalho', 'risco ocupacional', 'ergonomia'
    ]) or match_any(topic_norm, ['trabalhador', 'ocupacional']):
        return "Saúde do Trabalhador e Doenças Ocupacionais", 1.0, "Questão sobre saúde ocupacional, acidentes de trabalho (CAT), pneumoconioses ou doenças profissionais."

    # 8. Vigilância em Saúde e Notificação Compulsória (SINAN)
    if match_any(full_norm, [
        'notificacao compulsoria', 'sinan', 'ficha de notificacao', 'agravo de notificacao compulsoria',
        'lista nacional de notificacao', 'notificacao imediata', 'notificacao semanal', 'notificacao negativa',
        'sistema de informacao de agravos de notificacao', 'vigilancia sanitaria', 'anvisa', 'vigilancia ambiental',
        'vigilancia da saude do trabalhador', 'visat', 'sinasc', 'sim', 'declaracao de nascido vivo',
        'doenca de notificacao compulsoria', 'dnc', 'vigilancia em saude', 'sistemas de informacao em saude'
    ]) or match_any(topic_norm, ['notificacao', 'sinan', 'sistemas de informacao']):
        return "Vigilância em Saúde e Notificação Compulsória (SINAN)", 1.0, "Questão sobre sistemas de informação em saúde (SINAN, SIM, SINASC) e agravos de notificação compulsória."

    # 9. Vigilância Epidemiológica: Endemias, Epidemias e Surtos
    if match_any(full_norm, [
        'investigacao de surto', 'surto epidemico', 'taxa de ataque', 'coeficiente de ataque', 'taxa de ataque secundario',
        'caso indice', 'caso primario', 'caso secundario', 'curva epidemica', 'epidemia por fonte comum',
        'epidemia propagada', 'endemia', 'pandemia', 'diagrama de controle', 'nivel endemico', 'imunidade de rebanho',
        'bloqueio vacinal', 'quarentena', 'isolamento', 'medidas de controle de surto', 'canal endemico'
    ]) or match_any(topic_norm, ['surto', 'endemia', 'epidemia']):
        return "Vigilância Epidemiológica: Endemias, Epidemias e Surtos", 1.0, "Questão sobre investigação de surtos, dinâmica epidemiológica de epidemias e medidas de controle."

    # 10. História das Políticas de Saúde e Origens do SUS
    if match_any(full_norm, [
        'revolta da vacina', 'modelo sanitarista campanhista', 'oswaldo cruz', 'carlos chagas',
        'caixas de aposentadorias e pensoes', 'caps 1923', 'lei eloi chaves', 'institutos de aposentadorias e pensoes',
        'iaps', 'inps', 'inamps', 'movimento de reforma sanitaria', '8a conferencia nacional de saude',
        'oitava conferencia nacional de saude', 'previdencia social e saude', 'medicina previdenciaria',
        'sanitarismo campanhista', 'era vargas e a saude', 'historia da saude publica'
    ]) or match_any(topic_norm, ['historia da saude', 'origens do sus', 'reforma sanitaria']):
        return "História das Políticas de Saúde e Origens do SUS", 1.0, "Questão sobre evolução histórica das políticas de saúde pública no Brasil pré-SUS."

    # 11. Legislação, Diretrizes e Evolução do SUS
    if match_any(full_norm, [
        'lei 8.080', 'lei 8.142', 'lei 8080', 'lei 8142', 'decreto 7.508', 'decreto 7508',
        'constituicao federal de 1988', 'artigo 196', 'artigo 198', 'artigos 196 a 200',
        'universalidade', 'integralidade', 'equidade', 'descentralizacao', 'regionalizacao',
        'hierarquizacao', 'participacao da comunidade', 'controle social', 'conselho de saude',
        'conferencia de saude', 'paridade dos conselhos', 'fundo de saude', 'recursos do sus',
        'financiamento da saude', 'financiamento do sus', 'financiamento do sistema de saude',
        'nob 91', 'nob 93', 'nob 96', 'noas 2001', 'pacto pela saude 2006', 'contrato organizativo da acao publica',
        'coap', 'redes de atencao a saude', 'ras', 'emenda constitucional 95', 'lei complementar 141',
        'renases', 'rename', 'comissao intergestores bipartite', 'cib', 'cit', 'comissao intergestores tripartite',
        'mapa da saude', 'regiao de saude', 'operadoras de planos e seguros de saude', 'ans', 'rol da ans'
    ]) or match_any(topic_norm, ['legislacao', 'diretrizes do sus', 'constituicao', 'lei 8080', 'financiamento']):
        return "Legislação, Diretrizes e Evolução do SUS", 1.0, "Questão sobre arcabouço jurídico, diretrizes doutrinárias/organizativas, controle social e pactuação do SUS."

    # 12. História Natural da Doença e Níveis de Prevenção
    if match_any(full_norm, [
        'prevencao primaria', 'prevencao secundaria', 'prevencao terciaria', 'prevencao quaternaria',
        'prevencao primordial', 'historia natural da doenca', 'periodo pre-patogenico', 'periodo patogenico',
        'leavell e clark', 'promocao da saude', 'protecao especifica', 'diagnostico precoce', 'limitacao do dano',
        'reabilitacao', 'evitar iatrogenia e sobretratamento', 'quaternaria', 'sobrediagnostico', 'sobretratamento'
    ]) or match_any(topic_norm, ['niveis de prevencao', 'historia natural']):
        return "História Natural da Doença e Níveis de Prevenção", 1.0, "Questão sobre os níveis de prevenção em saúde (primária, secundária, terciária, quaternária) e história natural da doença."

    # 13. Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)
    return "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)", 0.95, "Questão sobre princípios da Atenção Primária à Saúde, ferramentas de abordagem familiar/comunitária (Genograma, Ecomapa) e funcionamento da ESF."

def run_audit(apply_changes=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Medicina Preventiva'
        ORDER BY q.id
    """).fetchall()
    
    print(f"Total de questões do Bloco 1 (Medicina Preventiva) analisadas: {len(rows)}")
    
    changes = []
    distribution = {}
    
    for r in rows:
        qid = r["id"]
        old_sub = r["subtema"]
        
        # Obter alternativas formatadas
        alts = conn.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)).fetchall()
        alts_text = " ".join([f"{a['letter']}) {a['text']}" for a in alts])
        
        q_dict = {
            "id": qid,
            "stem": r["stem"] or "",
            "topic": r["topic"] or "",
            "subtema_orig": r["subtema_orig"] or "",
            "area": r["area"] or "",
            "subtema": r["subtema"] or "",
            "explanation": r["explanation_text"] or "",
            "alternatives": alts_text
        }
        
        new_sub, conf, rationale = classify_preventiva_question(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale,
                "stem_snippet": (r["stem"] or "")[:90].strip()
            })
            
    print(f"\nTotal de reclassificações refinadas propostas no Bloco 1: {len(changes)}")
    print(f"\n--- NOVA DISTRIBUIÇÃO DOS 13 SUBTEMAS DO BLOCO 1 ---")
    for s, cnt in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {s}: {cnt} questões")
        
    print(f"\n--- AMOSTRA DE RECLASSIFICAÇÕES REFINADAS (20 PRIMEIROS CASOS) ---")
    for ch in changes[:20]:
        print(f"ID {ch['id']}: De '{ch['old_subtema']}' -> Para '{ch['new_subtema']}'")
        print(f"   Trecho: {ch['stem_snippet']}...")
        print(f"   Motivo: {ch['rationale']}\n")
        
    if apply_changes and changes:
        with conn:
            for ch in changes:
                conn.execute("""
                    UPDATE questions 
                    SET subtema = ?,
                        subtema_orig = CASE WHEN subtema_orig IS NULL OR subtema_orig = '' THEN subtema ELSE subtema_orig END
                    WHERE id = ?
                """, (ch["new_subtema"], ch["id"]))
        print(f"✅ {len(changes)} questões atualizadas no banco de dados com sucesso!")
        
    return changes, distribution

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    run_audit(apply_changes=apply_flag)
