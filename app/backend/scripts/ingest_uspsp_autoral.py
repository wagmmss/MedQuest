"""
Script de Ingestão e Otimização das 120 Questões Autorais do MEDCOF (USP-SP 2026).
- Mapeia para a taxonomia canônica oficial do MedQuest (170 temas).
- Estrutura comentários no Template Ouro (5 Pilares) sem links de vídeo Vimeo.
- Associa à banca oficial USP-SP com identificação autoral (editorial_status = 'autoral').
- Atualiza tabelas questions, alternatives, explanations e questions_fts.
- Executa sincronização incremental imediata com o Turso Cloud.
"""

import base64
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

HAR_PATH = r"C:\Users\wmors\Downloads\MEDCOF.har"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

MAPPINGS_120 = [
    # CIRURGIA (Q01 - Q24)
    (1, "Cirurgia", "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)"),
    (2, "Cirurgia", "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)"),
    (3, "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)"),
    (4, "Cirurgia", "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas"),
    (5, "Cirurgia", "Atendimento ao Paciente Queimado e Reposição Volêmica"),
    (6, "Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco"),
    (7, "Cirurgia", "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica"),
    (8, "Cirurgia", "Abdome Agudo Vascular e Isquemia Mesentérica"),
    (9, "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
    (10, "Cirurgia", "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica"),
    (11, "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
    (12, "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
    (13, "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
    (14, "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
    (15, "Cirurgia", "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)"),
    (16, "Cirurgia", "Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)"),
    (17, "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
    (18, "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
    (19, "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
    (20, "Cirurgia", "Cirurgia Bariátrica e Metabólica"),
    (21, "Cirurgia", "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)"),
    (22, "Cirurgia", "Oncologia Cutânea: Melanoma, CBC e CEC"),
    (23, "Cirurgia", "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana"),
    (24, "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)"),

    # CLÍNICA MÉDICA (Q25 - Q48)
    (25, "Clínica Médica", "Infecções Sexualmente Transmissíveis (ISTs) no Adulto"),
    (26, "Clínica Médica", "Diagnóstico Diferencial das Anemias e Hemoglobinopatias"),
    (27, "Clínica Médica", "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos"),
    (28, "Clínica Médica", "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica"),
    (29, "Clínica Médica", "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)"),
    (30, "Clínica Médica", "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)"),
    (31, "Clínica Médica", "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica"),
    (32, "Clínica Médica", "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica"),
    (33, "Clínica Médica", "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas"),
    (34, "Clínica Médica", "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas"),
    (35, "Clínica Médica", "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática"),
    (36, "Clínica Médica", "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas"),
    (37, "Clínica Médica", "Dermatoses Infecciosas, Hanseníase e Leishmanioses"),
    (38, "Clínica Médica", "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias"),
    (39, "Clínica Médica", "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)"),
    (40, "Clínica Médica", "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)"),
    (41, "Clínica Médica", "Meningites, Encefalites e Infecções do SNC"),
    (42, "Clínica Médica", "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento"),
    (43, "Clínica Médica", "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base"),
    (44, "Clínica Médica", "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)"),
    (45, "Clínica Médica", "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias"),
    (46, "Clínica Médica", "Leucemias, Linfomas e Mieloma Múltiplo"),
    (47, "Clínica Médica", "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)"),
    (48, "Clínica Médica", "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas"),

    # PEDIATRIA (Q49 - Q72)
    (49, "Pediatria", "Parasitoses Intestinais: Helmintíases e Protozooses"),
    (50, "Pediatria", "Cardiopatias Congênitas Cianogênicas e Acianogênicas"),
    (51, "Pediatria", "Baixa Estatura, Puberdade Precoce e Atraso Puberal"),
    (52, "Pediatria", "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas"),
    (53, "Pediatria", "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal"),
    (54, "Pediatria", "Reanimação Neonatal e Assistência em Sala de Parto"),
    (55, "Pediatria", "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância"),
    (56, "Pediatria", "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento"),
    (57, "Pediatria", "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas"),
    (58, "Pediatria", "Calendário Vacinal do PNI e Imunizações Especiais"),
    (59, "Pediatria", "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos"),
    (60, "Pediatria", "Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica"),
    (61, "Pediatria", "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite"),
    (62, "Pediatria", "Cardiopatias Congênitas Cianogênicas e Acianogênicas"),
    (63, "Pediatria", "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância"),
    (64, "Pediatria", "Infecção do Trato Urinário (ITU) e Refluxo Vesicoureteral na Infância"),
    (65, "Pediatria", "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil"),
    (66, "Pediatria", "Neonatologia: Icterícia Neonatal e Doenças Hematológicas"),
    (67, "Pediatria", "Imunodeficiências, Alergias e Anafilaxia na Infância"),
    (68, "Pediatria", "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas"),
    (69, "Pediatria", "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância"),
    (70, "Pediatria", "Constipação Intestinal Funcional e Orgânica"),
    (71, "Pediatria", "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite"),
    (72, "Pediatria", "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento"),

    # GINECOLOGIA E OBSTETRÍCIA (Q73 - Q90)
    (73, "Ginecologia e Obstetrícia", "Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal"),
    (74, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (75, "Ginecologia e Obstetrícia", "Assistência Pré-Natal de Baixo e Alto Risco"),
    (76, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (77, "Ginecologia e Obstetrícia", "Trabalho de Parto Prematuro e Tocólise"),
    (78, "Ginecologia e Obstetrícia", "Hemorragias da Primeira Metade: Abortamento, Ectópica e Mola"),
    (79, "Ginecologia e Obstetrícia", "Amniorrexe Prematura (RPMO) e Corioamnionite"),
    (80, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (81, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (82, "Ginecologia e Obstetrícia", "Diabetes Gestacional e Pré-Gestacional"),
    (83, "Ginecologia e Obstetrícia", "Puerpério Fisiológico, Patológico e Hemorragia Pós-Parto"),
    (84, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (85, "Ginecologia e Obstetrícia", "Infecções Perinatais e Transmissão Vertical (HIV, Sífilis, Hepatites, EGB)"),
    (86, "Ginecologia e Obstetrícia", "Doença Inflamatória Pélvica (DIP) e Atendimento à Violência Sexual"),
    (87, "Ginecologia e Obstetrícia", "Endometriose, Adenomiose e Dor Pélvica Crônica"),
    (88, "Ginecologia e Obstetrícia", "Rastreamento Citopatológico e Conduta em Lesões Cervicais (HPV)"),
    (89, "Ginecologia e Obstetrícia", "Massas Anexiais e Neoplasias Ovarianas"),
    (90, "Ginecologia e Obstetrícia", "Métodos Contraceptivos: Hormonais, DIU e Cirúrgicos"),

    # MEDICINA PREVENTIVA (Q91 - Q115)
    (91, "Medicina Preventiva", "Vigilância Epidemiológica: Endemias, Epidemias e Surtos"),
    (92, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (93, "Medicina Preventiva", "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística"),
    (94, "Medicina Preventiva", "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística"),
    (95, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (96, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (97, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (98, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (99, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (100, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (101, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (102, "Medicina Preventiva", "Legislação, Diretrizes e Evolução do SUS"),
    (103, "Medicina Preventiva", "História das Políticas de Saúde e Origens do SUS"),
    (104, "Medicina Preventiva", "Legislação, Diretrizes e Evolução do SUS"),
    (105, "Medicina Preventiva", "Legislação, Diretrizes e Evolução do SUS"),
    (106, "Medicina Preventiva", "História das Políticas de Saúde e Origens do SUS"),
    (107, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (108, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (109, "Medicina Preventiva", "Ética Médica, Bioética e Prontuários / Documentos"),
    (110, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (111, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (112, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (113, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (114, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (115, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),

    # COMPLEMENTARES (Q116 - Q120)
    (116, "Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco"),
    (117, "Clínica Médica", "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas"),
    (118, "Clínica Médica", "Diagnóstico Diferencial das Anemias e Hemoglobinopatias"),
    (119, "Clínica Médica", "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas"),
    (120, "Clínica Médica", "Hipertensão Arterial Sistêmica e Crises Hipertensivas")
]

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # remove all video tags, vimeo links, vumbnails
    text = re.sub(r'!\[video-tag-[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'!\[.*?\]\(https?://vumbnail\.com/[^)]*\)', '', text)
    text = re.sub(r'https?://player\.vimeo\.com/video/\d+[^\s\)\"\'>]*', '', text)
    text = re.sub(r'https?://vimeo\.com/\d+[^\s\)\"\'>]*', '', text)
    text = re.sub(r'#### Coment[aá]rio:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def build_golden_explanation(q):
    answers = q.get('answers', [])
    correct_idx = -1
    letters = ['A', 'B', 'C', 'D', 'E']
    for idx, a in enumerate(answers):
        if a.get('rightAnswer') is True:
            correct_idx = idx
            break
            
    correct_letter = letters[correct_idx] if correct_idx >= 0 else 'A'
    general_comment = clean_html(q.get('comment', ''))
    
    alt_explanations = {}
    for idx, a in enumerate(answers):
        let = letters[idx]
        c = clean_html(a.get('comment', ''))
        if c:
            alt_explanations[let] = c

    # Pulo do Gato
    pulo_do_gato = ""
    if general_comment:
        lines = [l.strip() for l in general_comment.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 20 and not line.startswith('#') and not line.startswith('|') and not line.startswith('Fonte:'):
                sentences = re.split(r'(?<=[.!?])\s+', line)
                if sentences:
                    pulo_do_gato = sentences[0]
                    if len(pulo_do_gato) < 50 and len(sentences) > 1:
                        pulo_do_gato += " " + sentences[1]
                    break
    
    if not pulo_do_gato and correct_letter in alt_explanations:
        pulo_do_gato = alt_explanations[correct_letter].split('.')[0] + "."

    correct_exp = alt_explanations.get(correct_letter, "")
    
    sections = []
    sections.append(f"**Gabarito**: Letra {correct_letter}")
    
    if pulo_do_gato:
        sections.append(f"**Pulo do Gato**: {pulo_do_gato.strip()}")
        
    if general_comment:
        sections.append(f"**Raciocínio Clínico e Fundamentação**:\n{general_comment}")
        
    if correct_exp:
        sections.append(f"**Por que a Letra {correct_letter} é a Correta?**:\n{correct_exp}")
        
    distratores = []
    for idx, a in enumerate(answers):
        let = letters[idx]
        if let != correct_letter:
            exp = alt_explanations.get(let, "Alternativa incorreta conforme discussão do caso clínico.")
            distratores.append(f"- **Letra {let}**: {exp}")
            
    if distratores:
        sections.append("**Análise dos Distratores**:\n" + "\n".join(distratores))
        
    return "\n\n".join(sections)

def main():
    print(f"=== INGESTÃO DE QUESTÕES AUTORAIS MEDCOF (USP-SP 2026) ===")
    print(f"Carregando arquivo HAR: {HAR_PATH}")
    
    with open(HAR_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    entries = data.get('log', {}).get('entries', [])
    raw_questions = []

    for entry in entries:
        url = entry.get('request', {}) .get('url', '')
        content = entry.get('response', {}).get('content', {})
        text = content.get('text', '')
        encoding = content.get('encoding', '')
        
        if '/qbank/full/' in url and text:
            if encoding == 'base64':
                text = base64.b64decode(text).decode('utf-8', errors='ignore')
            try:
                parsed = json.loads(text)
                for q in parsed.get('questions', []):
                    raw_questions.append(q)
            except Exception:
                pass

    # Sort and deduplicate
    raw_questions.sort(key=lambda x: x.get('index', 0))
    seen = set()
    unique_questions = []
    for q in raw_questions:
        idx = q.get('index')
        if idx not in seen:
            seen.add(idx)
            unique_questions.append(q)

    print(f"Total de questões únicas encontradas no HAR: {len(unique_questions)}")
    if len(unique_questions) != 120:
        print(f"[ERRO] Esperava 120 questões, encontrou {len(unique_questions)}.")
        return

    print(f"Conectando ao banco de dados local: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    source_file_name = "USP-SP 2026 AUTORAL"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Clean existing records for idempotency
    print(f"Removendo registros anteriores de '{source_file_name}' se existirem...")
    cur.execute("SELECT id FROM questions WHERE source_file = ?", (source_file_name,))
    existing_ids = [r['id'] for r in cur.fetchall()]
    if existing_ids:
        placeholders = ','.join('?' * len(existing_ids))
        cur.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", existing_ids)
        cur.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", existing_ids)
        cur.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", existing_ids)
        cur.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", existing_ids)
        print(f"Removidas {len(existing_ids)} questões antigas.")

    letters = ['A', 'B', 'C', 'D', 'E']
    inserted_count = 0

    for idx, q in enumerate(unique_questions):
        q_num = idx + 1
        map_num, area, subtema = MAPPINGS_120[idx]
        assert q_num == map_num

        sku = q.get('sku', '')
        tags = [t.get('name') for t in q.get('tags', []) if isinstance(t, dict)]
        subtema_orig = ", ".join(tags) if tags else ""
        stem = clean_html(q.get('statement', ''))
        
        answers = q.get('answers', [])
        correct_idx = 0
        for i, a in enumerate(answers):
            if a.get('rightAnswer') is True:
                correct_idx = i
                break
        correct_letter = letters[correct_idx]

        # 1. Insert into questions table
        cur.execute("""
            INSERT INTO questions (
                source_file, source_number, year, institution_code, institution_label,
                topic, stem, correct_letter, missing_alts, comment_code,
                area, subtema, subtema_orig, status, editorial_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_file_name,
            q_num,
            2026,
            "USP-SP",
            "USP - Universidade de São Paulo",
            subtema,
            stem,
            correct_letter,
            0,
            sku or q.get('questionIdentifier', ''),
            area,
            subtema,
            subtema_orig,
            "active",
            "autoral"
        ))
        
        question_id = cur.lastrowid

        # 2. Insert alternatives
        for i, a in enumerate(answers):
            let = letters[i]
            alt_text = clean_html(a.get('answer', ''))
            is_cor = 1 if (i == correct_idx) else 0
            cur.execute("""
                INSERT INTO alternatives (question_id, letter, text, is_correct)
                VALUES (?, ?, ?, ?)
            """, (question_id, let, alt_text, is_cor))

        # 3. Insert optimized golden explanation (NO VIMEO)
        explanation_text = build_golden_explanation(q)
        cur.execute("""
            INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at)
            VALUES (?, ?, ?, ?)
        """, (question_id, explanation_text, now_iso, now_iso))

        # 4. Insert into questions_fts if exists
        try:
            cur.execute("""
                INSERT INTO questions_fts (rowid, stem, explanation)
                VALUES (?, ?, ?)
            """, (question_id, stem, explanation_text))
        except Exception:
            pass

        inserted_count += 1

    conn.commit()
    print(f"\n[SUCESSO] Ingestão local concluída! {inserted_count} questões inseridas.")

    # Integrity verification
    cur.execute("SELECT COUNT(*) FROM questions WHERE source_file = ?", (source_file_name,))
    total_q = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alternatives WHERE question_id IN (SELECT id FROM questions WHERE source_file = ?)", (source_file_name,))
    total_alts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM explanations WHERE question_id IN (SELECT id FROM questions WHERE source_file = ?)", (source_file_name,))
    total_exp = cur.fetchone()[0]

    print("\n=== RESUMO DE INTEGRIDADE NO BANCO LOCAL ===")
    print(f"- Questões inseridas: {total_q} / 120")
    print(f"- Alternativas cadastradas: {total_alts} / 480")
    print(f"- Explicações Otimizadas: {total_exp} / 120")

    cur.execute("""
        SELECT area, COUNT(*) as count 
        FROM questions 
        WHERE source_file = ? 
        GROUP BY area
    """, (source_file_name,))
    print("\nDistribuição por Área:")
    for r in cur.fetchall():
        print(f"  - {r['area']}: {r['count']} questões")

    conn.close()

    # Sincronização incremental imediata com o Turso Cloud
    print("\n--- INICIANDO SINCRONIZAÇÃO INCREMENTAL COM TURSO CLOUD ---")
    try:
        from sync_incremental_turso import sync_incremental
        sync_incremental()
    except Exception as e:
        print("Erro no sync Turso automático:", e)

if __name__ == "__main__":
    main()
