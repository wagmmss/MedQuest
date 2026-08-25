"""
Script de Ingestão e Otimização das 100 Questões Autorais do MEDCOF (UNIFESP 2026).
- Mapeia para a taxonomia canônica oficial do MedQuest (170 temas).
- Estrutura comentários no Template Ouro (5 Pilares) sem links de vídeo Vimeo.
- Associa à banca oficial UNIFESP com identificação autoral (editorial_status = 'autoral').
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

MAPPINGS_UNIFESP = [
    # CIRURGIA (Q01 - Q20)
    (1, "Cirurgia", "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)"),
    (2, "Cirurgia", "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas"),
    (3, "Cirurgia", "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)"),
    (4, "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
    (5, "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)"),
    (6, "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)"),
    (7, "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
    (8, "Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco"),
    (9, "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
    (10, "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
    (11, "Cirurgia", "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)"),
    (12, "Cirurgia", "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)"),
    (13, "Cirurgia", "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)"),
    (14, "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
    (15, "Cirurgia", "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica"),
    (16, "Cirurgia", "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos"),
    (17, "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
    (18, "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
    (19, "Cirurgia", "Oncologia Cutânea: Melanoma, CBC e CEC"),
    (20, "Cirurgia", "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)"),

    # CLÍNICA MÉDICA (Q21 - Q40)
    (21, "Clínica Médica", "Leucemias, Linfomas e Mieloma Múltiplo"),
    (22, "Clínica Médica", "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio"),
    (23, "Clínica Médica", "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos"),
    (24, "Clínica Médica", "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)"),
    (25, "Clínica Médica", "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas"),
    (26, "Clínica Médica", "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)"),
    (27, "Clínica Médica", "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)"),
    (28, "Clínica Médica", "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)"),
    (29, "Clínica Médica", "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)"),
    (30, "Clínica Médica", "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas"),
    (31, "Clínica Médica", "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)"),
    (32, "Clínica Médica", "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base"),
    (33, "Clínica Médica", "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias"),
    (34, "Clínica Médica", "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas"),
    (35, "Clínica Médica", "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias"),
    (36, "Clínica Médica", "Vasculites Sistêmicas dos Grandes, Médios e Pequenos Vasos"),
    (37, "Clínica Médica", "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática"),
    (38, "Clínica Médica", "Hepatites Virais (A, B, C) e Icterícias Metabólicas"),
    (39, "Clínica Médica", "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas"),
    (40, "Clínica Médica", "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)"),

    # PEDIATRIA (Q41 - Q60)
    (41, "Pediatria", "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos"),
    (42, "Pediatria", "Anemias Carenciais e Distúrbios de Micronutrientes (Ferro, Vitamina D)"),
    (43, "Pediatria", "Infecção do Trato Urinário (ITU) e Refluxo Vesicoureteral na Infância"),
    (44, "Pediatria", "Calendário Vacinal do PNI e Imunizações Especiais"),
    (45, "Pediatria", "Arritmias, Síncope e Parada Cardiorrespiratória Pediátrica (PALS)"),
    (46, "Pediatria", "Cardiopatias Congênitas Cianogênicas e Acianogênicas"),
    (47, "Pediatria", "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite"),
    (48, "Pediatria", "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância"),
    (49, "Pediatria", "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância"),
    (50, "Pediatria", "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas"),
    (51, "Pediatria", "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas"),
    (52, "Pediatria", "Parasitoses Intestinais: Helmintíases e Protozooses"),
    (53, "Pediatria", "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas"),
    (54, "Pediatria", "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite"),
    (55, "Pediatria", "Vasculites na Infância (Henoch-Schönlein e Kawasaki)"),
    (56, "Pediatria", "Cardiopatias Congênitas Cianogênicas e Acianogênicas"),
    (57, "Pediatria", "Baixa Estatura, Puberdade Precoce e Atraso Puberal"),
    (58, "Pediatria", "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento"),
    (59, "Pediatria", "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal"),
    (60, "Pediatria", "Imunodeficiências, Alergias e Anafilaxia na Infância"),

    # GINECOLOGIA E OBSTETRÍCIA (Q61 - Q80)
    (61, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (62, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (63, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (64, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (65, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (66, "Ginecologia e Obstetrícia", "Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal"),
    (67, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (68, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (69, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (70, "Ginecologia e Obstetrícia", "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade"),
    (71, "Ginecologia e Obstetrícia", "Doença Inflamatória Pélvica (DIP) e Atendimento à Violência Sexual"),
    (72, "Ginecologia e Obstetrícia", "Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal"),
    (73, "Ginecologia e Obstetrícia", "Hemorragias da Primeira Metade: Abortamento, Ectópica e Mola"),
    (74, "Ginecologia e Obstetrícia", "Diabetes Gestacional e Pré-Gestacional"),
    (75, "Ginecologia e Obstetrícia", "Amniorrexe Prematura (RPMO) e Corioamnionite"),
    (76, "Ginecologia e Obstetrícia", "Puerpério Fisiológico, Patológico e Hemorragia Pós-Parto"),
    (77, "Ginecologia e Obstetrícia", "Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)"),
    (78, "Ginecologia e Obstetrícia", "Assistência Clínica ao Trabalho de Parto, Partograma e Distocias"),
    (79, "Ginecologia e Obstetrícia", "Assistência Pré-Natal de Baixo e Alto Risco"),
    (80, "Ginecologia e Obstetrícia", "Assistência Clínica ao Trabalho de Parto, Partograma e Distocias"),

    # MEDICINA PREVENTIVA (Q81 - Q100)
    (81, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (82, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (83, "Medicina Preventiva", "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística"),
    (84, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (85, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (86, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (87, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (88, "Medicina Preventiva", "Delineamentos e Classificação dos Estudos Epidemiológicos"),
    (89, "Medicina Preventiva", "Avaliação de Testes Diagnósticos e Curva ROC"),
    (90, "Medicina Preventiva", "Estudos Epidemiológicos: Medidas de Associação e Análise Estatística"),
    (91, "Medicina Preventiva", "Indicadores de Saúde e Coeficientes de Morbimortalidade"),
    (92, "Medicina Preventiva", "Vigilância Epidemiológica: Endemias, Epidemias e Surtos"),
    (93, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (94, "Medicina Preventiva", "Legislação, Diretrizes e Evolução do SUS"),
    (95, "Medicina Preventiva", "História Natural da Doença e Níveis de Prevenção"),
    (96, "Medicina Preventiva", "Legislação, Diretrizes e Evolução do SUS"),
    (97, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (98, "Medicina Preventiva", "Atenção Primária à Saúde e Estratégia Saúde da Família (ESF)"),
    (99, "Medicina Preventiva", "Saúde do Trabalhador e Doenças Ocupacionais"),
    (100, "Medicina Preventiva", "Ética Médica, Bioética e Prontuários / Documentos")
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
    print(f"=== INGESTÃO DE QUESTÕES AUTORAIS MEDCOF (UNIFESP 2026) ===")
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

    raw_questions.sort(key=lambda x: x.get('index', 0))
    seen = set()
    unique_questions = []
    for q in raw_questions:
        idx = q.get('index')
        if idx not in seen:
            seen.add(idx)
            unique_questions.append(q)

    print(f"Total de questões únicas encontradas no HAR: {len(unique_questions)}")
    if len(unique_questions) != 100:
        print(f"[ERRO] Esperava 100 questões, encontrou {len(unique_questions)}.")
        return

    print(f"Conectando ao banco de dados local: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    source_file_name = "UNIFESP 2026 AUTORAL"
    now_iso = datetime.now(timezone.utc).isoformat()

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
        map_num, area, subtema = MAPPINGS_UNIFESP[idx]
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
            "UNIFESP",
            "UNIFESP - Universidade Federal de São Paulo",
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
    print(f"- Questões inseridas: {total_q} / 100")
    print(f"- Alternativas cadastradas: {total_alts} / 400")
    print(f"- Explicações Otimizadas: {total_exp} / 100")

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

    # Sincronização incremental com o Turso Cloud
    print("\n--- INICIANDO SINCRONIZAÇÃO INCREMENTAL COM TURSO CLOUD ---")
    try:
        from sync_incremental_turso import sync_incremental
        sync_incremental()
    except Exception as e:
        print("Erro no sync Turso automático:", e)

if __name__ == "__main__":
    main()
