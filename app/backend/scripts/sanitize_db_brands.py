"""
MedQuest - Script de Sanitização e Higienização de Marcas no Banco de Dados
Remove qualquer menção a Medcof, Medway, Medcoffer, Medcofer, Medcoffers e derivados
das tabelas explanations, questions, alternatives, idempotency_keys e questions_fts.
"""
import os
import re
import sys
import shutil
import sqlite3
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))

def sanitize_text(text: str) -> str:
    if not text:
        return text

    # 1. Nome fictício de fármaco em estudos (ex: Q 16041)
    text = re.sub(r'\bMedcofimab\b', 'Investigumab', text)
    text = re.sub(r'\bmedcofimab\b', 'investigumab', text)
    text = re.sub(r'\bMEDCOFIMAB\b', 'INVESTIGUMAB', text)

    # 2. Cabeçalhos HTML / Callouts de atenção
    text = re.sub(r'<h4>\s*Aten[cç][aã]o\s+Medcoff?e*r*s*!\s*</h4>', '<h4>Atenção!</h4>', text, flags=re.IGNORECASE)
    text = re.sub(r'\*\*Aten[cç][aã]o\s+Medcoff?e*r*s*!\*\*', '**Atenção!**', text, flags=re.IGNORECASE)
    text = re.sub(r'Aten[cç][aã]o\s+Medcoff?e*r*s*!?', 'Atenção!', text, flags=re.IGNORECASE)

    # 3. Frases institucionais, referências a cursos e materiais
    text = re.sub(r'(?:Segundo|Conforme)\s+o\s+material\s+d[ao]\s+MedCof\b', 'Segundo as diretrizes de referência', text, flags=re.IGNORECASE)
    text = re.sub(r'Retirado\s+na\s+íntegra\s+de\s+nossa\s+Aula\s+MedCof\b', 'Diretrizes e literatura de referência', text, flags=re.IGNORECASE)
    text = re.sub(r'nossa\s+Aula\s+MedCof\b', 'conteúdo de referência', text, flags=re.IGNORECASE)
    text = re.sub(r'Aula\s+MedCof\b', 'aula de referência', text, flags=re.IGNORECASE)
    text = re.sub(r'material\s+d[ao]\s+MedCof\b', 'material de referência', text, flags=re.IGNORECASE)
    text = re.sub(r'equipe\s+(?:d[ao]\s+)?MedCof\b', 'equipe pedagógica', text, flags=re.IGNORECASE)
    text = re.sub(r'professores?\s+d[ao]\s+MedCof\b', 'professores', text, flags=re.IGNORECASE)
    text = re.sub(r'curso\s+MedCof\b', 'curso preparatório', text, flags=re.IGNORECASE)
    text = re.sub(r'banco\s+d[ao]\s+MedCof\b', 'banco de questões', text, flags=re.IGNORECASE)
    text = re.sub(r'simulados?\s+d[ao]\s+MedCof\b', 'simulado', text, flags=re.IGNORECASE)

    # 4. Tabelas e figuras elaboradas/criadas
    text = re.sub(r'Tabela\s+elaborada\s+pela\s+equipe\s+MedCof\s+e\s+adaptada\s+de\b', 'Tabela adaptada de', text, flags=re.IGNORECASE)
    text = re.sub(r'Tabela\s+criada\s+por\s+equipe\s+do\s+MedCof\.?', 'Tabela didática de referência.', text, flags=re.IGNORECASE)
    text = re.sub(r'Tabela\s+elaborada\s+pela\s+equipe\s+MedCof\.?', 'Tabela didática de referência.', text, flags=re.IGNORECASE)

    # 5. Processamento linha a linha
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        l_str = line.strip()
        
        # Encerramentos puros
        if re.search(r'^(?:[\*\_\s]*)?(?:Bons\s+estudos!?\s*)?(?:Com\s+carinho,?\s*)?(?:equipe\s+MedCof|time\s+MedCof|abra[cç]os?\s+d[ao]\s+MedCof)[\.\!\*\_\s]*$', l_str, re.IGNORECASE):
            if 'bons estudos' in l_str.lower():
                cleaned_lines.append('Bons estudos!')
            continue
        
        if re.search(r'^(?:[\*\_\s]*)?(?:Com\s+carinho,?\s*)?equipe\s+MedCof[\.\!\*\_\s]*$', l_str, re.IGNORECASE):
            continue

        # Atribuições e marcas d'água de imagens/tabelas
        if re.search(r'^(?:[\*\_\s\(\[]*)?(?:Fonte(?:\s+da\s+imagem)?|\(?[Ff]igura\s*\d*.*Fonte:?|Banco\s+de\s+imagens|Imagem\s*\d*.*Fonte:?)\s*[:\-–—]\s*(?:Acervo|Banco\s+de\s+imagens\s+)?MEDCOF[\.\*\_\)\]\s]*$', l_str, re.IGNORECASE):
            continue
        if re.search(r'^(?:[\*\_\s\(\[]*)?Fonte\s*:\s*(?:acervo(?:\s+de\s+imagens)?\s+)?Medcof\.?[\*\_\)\]\s]*$', l_str, re.IGNORECASE):
            continue
        if re.search(r'^(?:[\*\_\s\(\[]*)?Acervo\s+de\s+imagens\s+Medcof\.?[\*\_\)\]\s]*$', l_str, re.IGNORECASE):
            continue
        if re.search(r'^(?:[\*\_\s\(\[]*)?\*?Fonte\s*:\s*Medcof\.?\*?[\*\_\)\]\s]*$', l_str, re.IGNORECASE):
            continue

        # Limpeza de marcas d'água inline no final de parágrafos/legendas
        l_str = re.sub(r'[\.\s\-–—]*Fonte\s*:\s*(?:acervo(?:\s+de\s+imagens)?\s+|banco\s+de\s+imagens\s+|equipe\s+)?Medcof\.?', '.', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\.\s\-–—]*Banco\s+de\s+imagens\s+MEDCOF\.?', '.', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\.\s\-–—]*ACERVO\s+MEDCOF\.?', '.', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\.\s\-–—]*Acervo\s+MedCof\.?', '.', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\.\s\-–—]*Acervo\s+equipe\s+MedCof\.?', '.', l_str, flags=re.IGNORECASE)

        # Linhas isoladas de saudação
        if re.search(r'^(?:[\*\#\_\s]*)?(?:Fala|Ol[aá]|Oi|E\s+a[ií]|Salve|Querid[oa]|Caro)\s*,?\s*(?:aluno\s*)?Medcoff?e*r*s*!*[\*\_\s]*$', l_str, re.IGNORECASE):
            continue
        if re.search(r'^\*\*(?:Fala|Ol[aá]|Oi|E\s+a[ií]|Salve)\s*,?\s*medcoff?e*r*s*!\s*Vamos\s+aprender\s+com\s+essa\s+quest[aã]o\??\*\*', l_str, re.IGNORECASE):
            cleaned_lines.append('**Vamos analisar a questão:**')
            continue

        # Prefixo de saudação no início de frase
        greeting_prefix_regex = r'^(?:[\*\#\_\s]*)?(?:Fala|Ol[aá]|Oi|E\s+a[ií]|Salve|Querid[oa]|Caro)\s*,?\s*(?:aluno\s*)?Medcoff?e*r*s*[\!\,\.\:\s\-–—]+'
        if re.search(greeting_prefix_regex, l_str, re.IGNORECASE):
            l_str = re.sub(greeting_prefix_regex, '', l_str, flags=re.IGNORECASE).strip()
            if l_str:
                l_str = l_str[0].upper() + l_str[1:]

        # Vocativo no início da linha
        vocative_regex = r'^(?:[\*\#\_\s]*)?Medcoff?e*r*s*[\!\,\:\s\-–—]+'
        if re.search(vocative_regex, l_str, re.IGNORECASE):
            l_str = re.sub(vocative_regex, '', l_str, flags=re.IGNORECASE).strip()
            if l_str:
                l_str = l_str[0].upper() + l_str[1:]

        # Vocativos no meio de frases
        l_str = re.sub(r'Resumindo\s*,?\s*Medcoff?e*r*s*\s*:', 'Resumindo:', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\,\s]+hein\s*,?\s*Medcoff?e*r*s*\b', '', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'[\,\s]+Medcoff?e*r*s*([\,\.\!\?])', r'\1', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'\bMedcoff?e*r*s*[\,\s]+', '', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'\baluno\s+medcof\b', 'candidato', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'\balunos\s+medcof\b', 'candidatos', l_str, flags=re.IGNORECASE)

        # Menções residuais
        l_str = re.sub(r'\bMedCof\b', 'MedQuest', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'\bMedway\b', 'MedQuest', l_str, flags=re.IGNORECASE)
        l_str = re.sub(r'\bMedcoff?e*r*s*\b', 'candidatos', l_str, flags=re.IGNORECASE)

        if l_str or not line:
            cleaned_lines.append(l_str)

    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result).strip()
    return result

def main():
    print("=" * 70)
    print("MEDQUEST - SANITIZAÇÃO DE MARCAS NO BANCO DE DADOS")
    print("=" * 70)
    print(f"Alvo do banco: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"[ERRO] Banco de dados não encontrado em {DB_PATH}")
        sys.exit(1)

    # 1. Backup Físico
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    backup_path = os.path.join(BACKEND_DIR, f"medquest.db.backup_pre_brand_sanitization_{timestamp}")
    print(f"\n[1/7] Criando backup de segurança em:\n  -> {backup_path}")
    shutil.copy2(DB_PATH, backup_path)
    print("  [OK] Backup criado com sucesso.")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")

        # 2. Sanitizar Explanations
        print("\n[2/7] Sanitizando comentários e explicações (explanations.explanation_text)...")
        cur.execute("SELECT question_id, explanation_text FROM explanations WHERE explanation_text LIKE '%medcof%' OR explanation_text LIKE '%medway%'")
        exp_rows = cur.fetchall()
        print(f"  -> {len(exp_rows)} registros com potenciais menções encontrados.")
        
        updated_exps = 0
        for row in exp_rows:
            qid = row['question_id']
            orig_text = row['explanation_text'] or ""
            cleaned_text = sanitize_text(orig_text)
            if cleaned_text != orig_text:
                cur.execute("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", (cleaned_text, qid))
                updated_exps += 1
        print(f"  [OK] {updated_exps} explicações atualizadas com sucesso.")

        # 3. Sanitizar Enunciados (questions.stem)
        print("\n[3/7] Sanitizando enunciados de questões (questions.stem)...")
        cur.execute("SELECT id, stem FROM questions WHERE stem LIKE '%medcof%' OR stem LIKE '%medway%'")
        stem_rows = cur.fetchall()
        print(f"  -> {len(stem_rows)} questões com potenciais menções encontradas.")
        
        updated_stems = 0
        for row in stem_rows:
            qid = row['id']
            orig_stem = row['stem'] or ""
            cleaned_stem = sanitize_text(orig_stem)
            if cleaned_stem != orig_stem:
                cur.execute("UPDATE questions SET stem = ? WHERE id = ?", (cleaned_stem, qid))
                updated_stems += 1
        print(f"  [OK] {updated_stems} enunciados atualizados com sucesso.")

        # 4. Sanitizar Arquivos de Origem (questions.source_file)
        print("\n[4/7] Sanitizando arquivos de origem (questions.source_file)...")
        cur.execute("SELECT id, source_file FROM questions WHERE source_file LIKE '%medway%' OR source_file LIKE '%medcof%'")
        sf_rows = cur.fetchall()
        print(f"  -> {len(sf_rows)} registros em source_file com prefixos encontrados.")
        
        updated_sf = 0
        for row in sf_rows:
            qid = row['id']
            orig_sf = row['source_file'] or ""
            cleaned_sf = re.sub(r'^MEDWAY\s+', '', orig_sf, flags=re.IGNORECASE).strip()
            cleaned_sf = re.sub(r'^MEDCOF\s+', '', cleaned_sf, flags=re.IGNORECASE).strip()
            if cleaned_sf != orig_sf:
                cur.execute("UPDATE questions SET source_file = ? WHERE id = ?", (cleaned_sf, qid))
                updated_sf += 1
        print(f"  [OK] {updated_sf} source_files atualizados com sucesso.")

        # 5. Sanitizar Códigos de Referência (questions.comment_code)
        print("\n[5/7] Sanitizando comment_code (questions.comment_code)...")
        cur.execute("SELECT id, comment_code FROM questions WHERE comment_code LIKE '%medway%' OR comment_code LIKE '%medcof%'")
        cc_rows = cur.fetchall()
        print(f"  -> {len(cc_rows)} registros em comment_code encontrados.")
        
        updated_cc = 0
        for row in cc_rows:
            qid = row['id']
            orig_cc = row['comment_code'] or ""
            cleaned_cc = re.sub(r'^medway:', 'mw:', orig_cc, flags=re.IGNORECASE)
            cleaned_cc = re.sub(r'^medcof:', 'mc:', cleaned_cc, flags=re.IGNORECASE)
            if cleaned_cc != orig_cc:
                cur.execute("UPDATE questions SET comment_code = ? WHERE id = ?", (cleaned_cc, qid))
                updated_cc += 1
        print(f"  [OK] {updated_cc} comment_codes normalizados com sucesso.")

        # 6. Sanitizar Alternativas (alternatives.text)
        print("\n[6/7] Sanitizando alternativas (alternatives.text)...")
        cur.execute("SELECT id, text FROM alternatives WHERE text LIKE '%medcof%' OR text LIKE '%medway%'")
        alt_rows = cur.fetchall()
        print(f"  -> {len(alt_rows)} alternativas encontradas.")
        
        updated_alts = 0
        for row in alt_rows:
            aid = row['id']
            orig_alt = row['text'] or ""
            cleaned_alt = sanitize_text(orig_alt)
            if cleaned_alt != orig_alt:
                cur.execute("UPDATE alternatives SET text = ? WHERE id = ?", (cleaned_alt, aid))
                updated_alts += 1
        print(f"  [OK] {updated_alts} alternativas atualizadas com sucesso.")

        # Limpar chaves legadas de idempotência
        cur.execute("DELETE FROM idempotency_keys WHERE response_body LIKE '%medcof%' OR response_body LIKE '%medway%'")
        deleted_idemp = cur.rowcount
        print(f"  [OK] {deleted_idemp} registros de cache em idempotency_keys limpos.")

        # 7. Reconstruir Índice FTS5 (questions_fts)
        print("\n[7/7] Reconstruindo índice de busca full-text (questions_fts)...")
        try:
            cur.execute("DELETE FROM questions_fts")
            cur.execute("""
                INSERT INTO questions_fts (rowid, stem, explanation)
                SELECT q.id, q.stem, e.explanation_text
                FROM questions q
                LEFT JOIN explanations e ON q.id = e.question_id
            """)
            print("  [OK] questions_fts reindexado com sucesso.")
        except Exception as e:
            print(f"  [AVISO] Erro na reindexação FTS: {e}")

        conn.commit()
        print("\n" + "=" * 70)
        print("TRANSAÇÃO CONCLUÍDA E SALVA COM SUCESSO (COMMIT)")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO CRÍTICO] Falha durante a sanitização. Transação revertida (ROLLBACK): {e}")
        conn.close()
        sys.exit(1)

    # Auditoria de Verificação Pós-Migração
    print("\n--- AUDITORIA PÓS-MIGRAÇÃO ---")
    
    # 1. Explanations não-URL
    cur.execute("SELECT question_id, explanation_text FROM explanations")
    exp_left = 0
    for r in cur.fetchall():
        txt = r['explanation_text'] or ""
        txt_no_url = re.sub(r'https?://[^\s\)\"\>]+', '', txt)
        if re.search(r'medcof|medway', txt_no_url, re.IGNORECASE):
            exp_left += 1

    # 2. Stems não-URL
    cur.execute("SELECT id, stem FROM questions")
    stem_left = 0
    for r in cur.fetchall():
        txt = r['stem'] or ""
        txt_no_url = re.sub(r'https?://[^\s\)\"\>]+', '', txt)
        if re.search(r'medcof|medway', txt_no_url, re.IGNORECASE):
            stem_left += 1

    # 3. Source files
    cur.execute("SELECT COUNT(*) FROM questions WHERE source_file LIKE '%medway%' OR source_file LIKE '%medcof%'")
    sf_left = cur.fetchone()[0]

    # 4. Comment codes
    cur.execute("SELECT COUNT(*) FROM questions WHERE comment_code LIKE '%medway%' OR comment_code LIKE '%medcof%'")
    cc_left = cur.fetchone()[0]

    # 5. Alternatives não-URL
    cur.execute("SELECT id, text FROM alternatives")
    alt_left = 0
    for r in cur.fetchall():
        txt = r['text'] or ""
        txt_no_url = re.sub(r'https?://[^\s\)\"\>]+', '', txt)
        if re.search(r'medcof|medway', txt_no_url, re.IGNORECASE):
            alt_left += 1

    print(f"Explanations (texto não-URL residual): {exp_left}")
    print(f"Stems (texto não-URL residual):        {stem_left}")
    print(f"Source files residuais:               {sf_left}")
    print(f"Comment codes residuais:              {cc_left}")
    print(f"Alternatives (texto não-URL residual): {alt_left}")

    conn.close()

    if exp_left == 0 and stem_left == 0 and sf_left == 0 and cc_left == 0 and alt_left == 0:
        print("\n[SUCESSO ABSOLUTO] Todas as menções de texto a Medcof e Medway foram completamente eliminadas!")
    else:
        print("\n[AVISO] Ainda restam algumas ocorrências residuais.")

if __name__ == "__main__":
    main()
