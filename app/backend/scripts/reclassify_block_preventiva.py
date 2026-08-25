"""
Classificador de Alta Precisão - Bloco 1: Medicina Preventiva (13 Subtemas Canônicos)
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

def classify_preventiva(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    sub_orig_norm = norm(subtema_orig)
    full_norm = norm(f"{stem} {topic} {subtema_orig}")
    exp_norm = norm(exp[:500])

    # 1. Declaração de Óbito e Ética Médica / Bioética
    if match_any(stem_norm, [
        'declaracao de obito', 'declaracoes de obito', 'atestado de obito', 'atestados de obito', 
        'preenchimento da declaracao de obito', 'causa basica da morte', 'causa terminal', 'causa intermediaria',
        'sigilo medico', 'segredo medico', 'quebra de sigilo', 'termo de consentimento', 'tcle',
        'diretivas antecipadas de vontade', 'testamento vital', 'codigo de etica medica', 'cem',
        'conselho regional de medicina', 'conselho federal de medicina', 'crm', 'cfm',
        'iatrogenia', 'impericia', 'imprudencia', 'negligencia', 'guarda do prontuario', 'prontuario medico',
        'servico de verificacao de obito', 'svo', 'instituto medico legal', 'iml', 'morte suspeita', 'morte violenta'
    ]) or (match_any(topic_norm, ['etica', 'bioetica', 'obito', 'atestado', 'sigilo', 'prontuario']) and not match_any(stem_norm, ['coeficiente de mortalidade', 'taxa de mortalidade'])):
        return "Ética Médica, Bioética e Prontuários / Documentos", 1.0, "Ética médica, bioética, sigilo ou preenchimento de declaração de óbito."

    # 2. Avaliação de Testes Diagnósticos e Curva ROC
    if match_any(stem_norm, [
        'sensibilidade', 'especificidade', 'valor preditivo positivo', 'valor preditivo negativo', 'vpp', 'vpn',
        'curva roc', 'area sob a curva roc', 'razao de verossimilhanca', 'likelihood ratio', 'acuracia',
        'ponto de corte', 'falso positivo', 'falso negativo', 'verdadeiro positivo', 'verdadeiro negativo',
        'testes em paralelo', 'testes em serie', 'teste de triagem', 'teste confirmatorio', 'coeficiente kappa',
        'concordancia interobservador', 'tabela 2x2'
    ]) or match_any(topic_norm, ['testes diagnosticos', 'curva roc', 'sensibilidade', 'especificidade']):
        return "Avaliação de Testes Diagnósticos e Curva ROC", 1.0, "Avaliação de testes diagnósticos, acurácia e curva ROC."

    # 3. Estudos Epidemiológicos: Medidas de Associação e Análise Estatística
    if match_any(stem_norm, [
        'risco relativo', 'razao de chances', 'odds ratio', 'risco atribuivel', 'reducao absoluta do risco',
        'reducao relativa do risco', 'numero necessario para tratar', 'nnt', 'numero necessario para causar dano',
        'nnh', 'intervalo de confianca', 'valor p', 'erro tipo i', 'erro tipo ii', 'erro alfa', 'erro beta',
        'poder estatistico', 'teste t de student', 'qui-quadrado', 'qui quadrado', 'regressao linear', 'regressao logistica',
        'fator de confusao', 'confundimento', 'vies de selecao', 'vies de afericao', 'vies de memoria', 'vies de informacao',
        'modificacao de efeito', 'analise por intencao de tratar'
    ]) or match_any(topic_norm, ['medidas de associacao', 'bioestatistica', 'analise estatistica']):
        return "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística", 1.0, "Medidas de associação e análise estatística epidemiológica."

    # 4. Delineamentos e Classificação dos Estudos Epidemiológicos
    if match_any(stem_norm, [
        'estudo de coorte', 'estudo caso-controle', 'estudo de caso-controle', 'ensaio clinico randomizado',
        'ensaio clinico controlado', 'estudo transversal', 'estudo seccional', 'estudo ecologico', 'falacia ecologica',
        'revisao sistematica', 'meta-analise', 'metanalise', 'duplo-cego', 'longitudinal', 'delineamento do estudo', 
        'tipo de estudo', 'desenho do estudo', 'ensaio comunitário', 'estudo de intervencao'
    ]) or match_any(topic_norm, ['delineamento', 'tipo de estudo', 'estudos epidemiologicos', 'desenho']):
        return "Delineamentos e Classificação dos Estudos Epidemiológicos", 1.0, "Desenho e classificação de estudos epidemiológicos."

    # 5. Indicadores de Saúde e Coeficientes de Morbimortalidade
    if match_any(stem_norm, [
        'coeficiente de mortalidade', 'taxa de mortalidade infantil', 'taxa de mortalidade materna',
        'mortalidade neonatal precoce', 'mortalidade neonatal tardia', 'mortalidade pos-neonatal',
        'mortalidade perinatal', 'indice de swaroop-uemura', 'curva de nelson moraes', 'mortalidade proporcional',
        'anos potenciais de vida perdidos', 'apvp', 'daly', 'qaly', 'taxa de letalidade', 'coeficiente de letalidade',
        'coeficiente de natalidade', 'razao de mortalidade materna', 'indicadores de saude', 'indicadores demograficos',
        'padronizacao de taxas', 'padronizacao direta', 'padronizacao indireta'
    ]) or match_any(topic_norm, ['indicadores', 'coeficientes', 'morbimortalidade']):
        return "Indicadores de Saúde e Coeficientes de Morbimortalidade", 1.0, "Indicadores de saúde e coeficientes de morbimortalidade."

    # 6. Transição Demográfica e Perfis Populacionais
    if match_any(stem_norm, [
        'transicao demografica', 'transicao epidemiologica', 'piramide etaria', 'envelhecimento populacional',
        'taxa de fecundidade', 'razao de dependencia', 'indice de envelhecimento', 'dupla carga de doencas', 
        'tripla carga de doencas', 'esperanca de vida ao nascer', 'expectativa de vida', 'bonus demografico'
    ]) or match_any(topic_norm, ['transicao', 'demografia']):
        return "Transição Demográfica e Perfis Populacionais", 1.0, "Transição demográfica e perfis populacionais."

    # 7. Saúde do Trabalhador e Doenças Ocupacionais
    if match_any(stem_norm, [
        'saude do trabalhador', 'doenca ocupacional', 'doenca profissional', 'acidente de trabalho',
        'comunicacao de acidente de trabalho', 'cat', 'nexo tecnico epidemiologico', 'netep',
        'perda auditiva induzida por ruido', 'pair', 'ler/dort', 'ler-dort', 'tenossinovite ocupacional',
        'silicose', 'asbestose', 'pneumoconiose', 'saturnismo', 'intoxicacao por chumbo ocupacional',
        'intoxicacao por mercurio', 'hidrargirismo', 'intoxicacao por benzeno', 'benzenismo', 'asbesto',
        'amianto', 'mesotelioma ocupacional', 'nr-32', 'nr 32', 'norma regulamentadora', 'burnout ocupacional',
        'cerest', 'centro de referencia em saude do trabalhador', 'inss', 'auxilio-doenca acidentario'
    ]) or match_any(topic_norm, ['trabalhador', 'ocupacional']):
        return "Saúde do Trabalhador e Doenças Ocupacionais", 1.0, "Saúde ocupacional e acidentes/doenças do trabalho."

    # 8. Vigilância em Saúde e Notificação Compulsória (SINAN)
    if match_any(stem_norm, [
        'notificacao compulsoria', 'sinan', 'ficha de notificacao', 'agravo de notificacao compulsoria',
        'lista nacional de notificacao', 'notificacao imediata', 'notificacao semanal', 'notificacao negativa',
        'sistema de informacao de agravos de notificacao', 'vigilancia sanitaria', 'anvisa', 'vigilancia ambiental',
        'vigilancia da saude do trabalhador', 'visat', 'sinasc', 'sim', 'declaracao de nascido vivo',
        'doenca de notificacao compulsoria'
    ]) or match_any(topic_norm, ['notificacao', 'sinan', 'sistemas de informacao']):
        return "Vigilância em Saúde e Notificação Compulsória (SINAN)", 1.0, "Vigilância em saúde e notificação compulsória (SINAN)."

    # 9. Vigilância Epidemiológica: Endemias, Epidemias e Surtos
    if match_any(stem_norm, [
        'investigacao de surto', 'surto epidemico', 'taxa de ataque', 'coeficiente de ataque', 'taxa de ataque secundario',
        'caso indice', 'caso primario', 'caso secundario', 'curva epidemica', 'epidemia por fonte comum',
        'epidemia propagada', 'endemia', 'pandemia', 'diagrama de controle', 'nivel endemico', 'imunidade de rebanho',
        'bloqueio vacinal', 'canal endemico'
    ]) or match_any(topic_norm, ['surto', 'endemia', 'epidemia']):
        return "Vigilância Epidemiológica: Endemias, Epidemias e Surtos", 1.0, "Investigação de surtos, epidemias e endemias."

    # 10. História das Políticas de Saúde e Origens do SUS
    if match_any(stem_norm, [
        'revolta da vacina', 'modelo sanitarista campanhista', 'oswaldo cruz', 'carlos chagas',
        'caixas de aposentadorias e pensoes', 'caps 1923', 'lei eloi chaves', 'institutos de aposentadorias e pensoes',
        'iaps', 'inps', 'inamps', 'movimento de reforma sanitaria', '8a conferencia nacional de saude',
        'oitava conferencia nacional de saude', 'previdencia social e saude', 'sanitarismo campanhista'
    ]) or match_any(topic_norm, ['historia da saude', 'origens do sus', 'reforma sanitaria']):
        return "História das Políticas de Saúde e Origens do SUS", 1.0, "História da saúde pública e evolução até a criação do SUS."

    # 11. Legislação, Diretrizes e Evolução do SUS
    if match_any(stem_norm, [
        'lei 8.080', 'lei 8.142', 'lei 8080', 'lei 8142', 'decreto 7.508', 'decreto 7508',
        'constituicao federal de 1988', 'artigo 196', 'artigo 198', 'artigos 196 a 200',
        'universalidade', 'integralidade', 'equidade', 'descentralizacao', 'regionalizacao',
        'hierarquizacao', 'participacao da comunidade', 'controle social', 'conselho de saude',
        'conferencia de saude', 'paridade dos conselhos', 'fundo de saude', 'recursos do sus',
        'financiamento da saude', 'financiamento do sus', 'financiamento do sistema de saude',
        'nob 91', 'nob 93', 'nob 96', 'noas 2001', 'pacto pela saude 2006', 'contrato organizativo da acao publica',
        'coap', 'redes de atencao a saude', 'ras', 'emenda constitucional 95', 'lei complementar 141',
        'renases', 'rename', 'comissao intergestores bipartite', 'cib', 'cit', 'comissao intergestores tripartite',
        'mapa da saude', 'regiao de saude', 'saude suplementar', 'ans', 'planos de saude', 'lei 9.656'
    ]) or match_any(topic_norm, ['legislacao', 'diretrizes do sus', 'constituicao', 'lei 8080', 'financiamento', 'saude privada e suplementar']):
        return "Legislação, Diretrizes e Evolução do SUS", 1.0, "Legislação, diretrizes, financiamento e regulação do SUS/Saúde Suplementar."

    # 12. História Natural da Doença e Níveis de Prevenção
    if match_any(stem_norm, [
        'prevencao primaria', 'prevencao secundaria', 'prevencao terciaria', 'prevencao quaternaria',
        'prevencao primordial', 'historia natural da doenca', 'periodo pre-patogenico', 'periodo patogenico',
        'leavell e clark', 'promocao da saude', 'protecao especifica', 'diagnostico precoce', 'limitacao do dano',
        'reabilitacao', 'evitar iatrogenia e sobretratamento', 'quaternaria', 'sobrediagnostico', 'sobretratamento'
    ]) or match_any(topic_norm, ['niveis de prevencao', 'historia natural', 'prevencao quaternaria']):
        return "História Natural da Doença e Níveis de Prevenção", 1.0, "Níveis de prevenção em saúde e história natural da doença."

    # 13. Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)
    return "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)", 0.95, "Princípios da Atenção Primária à Saúde, abordagem familiar/comunitária e funcionamento da ESF."

def process_block1(apply=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Medicina Preventiva'
        ORDER BY q.id
    """).fetchall()
    
    print(f"==================================================")
    print(f"PROCESSANDO BLOCO 1: MEDICINA PREVENTIVA ({len(rows)} QUESTÕES)")
    print(f"Modo: {'APLICAÇÃO DIRETA NO BANCO' if apply else 'AUDITORIA / SIMULAÇÃO'}")
    print(f"==================================================")
    
    changes = []
    distribution = {}
    
    for r in rows:
        qid = r["id"]
        old_sub = r["subtema"]
        
        q_dict = {
            "id": qid,
            "stem": r["stem"] or "",
            "topic": r["topic"] or "",
            "subtema_orig": r["subtema_orig"] or "",
            "area": r["area"] or "",
            "subtema": r["subtema"] or "",
            "explanation": r["explanation_text"] or "",
        }
        
        new_sub, conf, rationale = classify_preventiva(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale
            })
            
    print(f"\nTotal de reclassificações no Bloco 1: {len(changes)} ({len(changes)/len(rows)*100:.1f}%)")
    print(f"\n--- DISTRIBUIÇÃO DOS 13 SUBTEMAS DO BLOCO 1 ---")
    for s, cnt in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {s}: {cnt} questões")
        
    if apply and changes:
        with conn:
            for ch in changes:
                conn.execute("""
                    UPDATE questions 
                    SET subtema = ?,
                        subtema_orig = CASE WHEN subtema_orig IS NULL OR subtema_orig = '' THEN subtema ELSE subtema_orig END
                    WHERE id = ?
                """, (ch["new_subtema"], ch["id"]))
        print(f"\n✅ {len(changes)} questões do Bloco 1 atualizadas no banco com sucesso!")
        
    return changes

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    process_block1(apply=apply_flag)
