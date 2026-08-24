"""
Script de correção de rótulos e códigos de instituições no banco SQLite.
Extrai as tags reais diretamente de cada página dos PDFs originais
e atualiza a tabela 'questions' associando cada questão à sua instituição correta.
"""
import os
import re
import sqlite3
import pymupdf

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
DOCS_DIR = os.environ.get("MEDQUEST_PDF_DIR", os.path.join(PROJECT_ROOT, "documentos"))
if not os.path.exists(DOCS_DIR):
    DOCS_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "documentos")

PDF_FILE_MAPPING = {
    "SÍRIO EINSTEIN E SCMSP 2020 A 2023.pdf": "SÍRIO EINSTEIN E SCMSP 2020 A 2023",
    "SÍRIO EINSTEIN E SCMSP 2024 A 2026.pdf": "SÍRIO EINSTEIN E SCMSP 2024 A 2026",
    "UNIFESP E UNICAMP 2020 A 2022.pdf": "UNIFESP E UNICAMP 2020 A 2022",
    "UNIFESP E UNICAMP 2023 A 2026.pdf": "UNIFESP E UNICAMP 2023 A 2026",
    "USP 2020 a 2023.pdf": "USP 2020 a 2023",
    "USP 2024 a 2026.pdf": "USP 2024 a 2026",
}

def classify_tags(tags_list, default_pdf_inst=None):
    tag_str = " ".join(tags_list)
    tag_upper = tag_str.upper()

    # 1. Hospital Sírio-Libanês / HSL
    if "HOSPITAL SÍRIO" in tag_upper or "SÍRIO-LIBANÊS" in tag_upper or "SIRIO" in tag_upper or " HSL" in tag_str or "- HSL" in tag_str or "HSL " in tag_str:
        return "HSL", "Hospital Sírio-Libanês (HSL)"

    # 2. Einstein / HIAE
    if "ALBERT EINSTEIN" in tag_upper or "EINSTEIN" in tag_upper or "HIAE" in tag_str:
        return "EINSTEIN", "Hospital Israelita Albert Einstein (HIAE)"

    # 3. Santa Casa de SP / SCMSP
    if "SANTA CASA" in tag_upper or "SCMSP" in tag_str:
        return "SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"

    # 4. SUS-SP
    if "SUS SP" in tag_upper or "SUS-SP" in tag_upper or "SISTEMA ÚNICO DE SAÚDE" in tag_upper or "SISTEMA UNICO DE SAUDE" in tag_upper or "STRIX" in tag_upper:
        return "SUS-SP", "SUS-SP - Seleção Unificada para Residência Médica do Estado de São Paulo"

    # 5. UNICAMP
    if "CAMPINAS" in tag_upper or "UNICAMP" in tag_upper or "FCM" in tag_str:
        return "UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"

    # 6. UNIFESP
    if "UNIFESP" in tag_upper or "PAULISTA DE MEDICINA" in tag_upper or "UNIVERSIDADE FEDERAL DE SÃO PAULO" in tag_upper or "UNIVERSIDADE FEDERAL DE SAO PAULO" in tag_upper or "EPM" in tag_str:
        return "UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"

    # 7. USP - Ribeirão Preto
    if "RIBEIRÃO PRETO" in tag_upper or "RIBEIRAO PRETO" in tag_upper or "USP-RP" in tag_upper or "HCRP" in tag_upper or "FMRP" in tag_upper:
        return "USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"

    # 8. HRAC-USP (Bauru)
    if "HRAC" in tag_upper or "BAURU" in tag_upper or "CRANIOFACIAIS" in tag_upper:
        return "HRAC-USP", "USP - Hospital de Reabilitação de Anomalias Craniofaciais (HRAC), Bauru"

    # 9. USP - São Paulo (HC-FMUSP)
    if "USP" in tag_upper or "HC-FMUSP" in tag_upper or "FMUSP" in tag_upper:
        return "USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"

    if default_pdf_inst:
        return default_pdf_inst

    return "OUTRO", "Instituição não identificada"


def extract_institutions_from_pdf(pdf_path, pdf_filename):
    doc = pymupdf.open(pdf_path)
    all_q_tags = {}
    current_q = None
    current_tags = []

    for pno in range(len(doc)):
        page = doc[pno]
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4]
            lines = text.split("\n")
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                m = re.match(r"^Quest[aã]o\s+(\d+)", line_str)
                if m:
                    if current_q is not None:
                        all_q_tags[current_q] = current_tags
                    current_q = int(m.group(1))
                    current_tags = []
                else:
                    if current_q is not None:
                        current_tags.append(line_str)
    if current_q is not None:
        all_q_tags[current_q] = current_tags

    # Definir fallback por padrão de PDF quando tags são repetitivas
    default_pdf_inst = None
    if "USP" in pdf_filename:
        default_pdf_inst = ("USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)")

    results = {}
    for qnum, tags in all_q_tags.items():
        code, label = classify_tags(tags, default_pdf_inst)
        results[qnum] = (code, label)

    return results


def run():
    print(f"Conectando ao banco de dados: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("\n--- DISTRIBUIÇÃO ATUAL (ANTES) ---")
    cur.execute("SELECT institution_code, institution_label, COUNT(*) as cnt FROM questions GROUP BY institution_code, institution_label ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['institution_code']}: {r['cnt']} ({r['institution_label']})")

    updates = []

    # 1. Processar PDFs em documentos/
    for pdf_fname, source_file_db in PDF_FILE_MAPPING.items():
        pdf_path = os.path.join(DOCS_DIR, pdf_fname)
        if not os.path.exists(pdf_path):
            print(f"AVISO: PDF não encontrado em {pdf_path}")
            continue

        print(f"\nProcessando {pdf_fname}...")
        inst_map = extract_institutions_from_pdf(pdf_path, pdf_fname)
        print(f"  Extraídas {len(inst_map)} questões do PDF.")

        # Buscar questões correspondentes no banco
        cur.execute("SELECT id, source_number, institution_code FROM questions WHERE source_file = ?", (source_file_db,))
        db_rows = cur.fetchall()

        matched = 0
        changed = 0
        for row in db_rows:
            sn = row["source_number"]
            if sn in inst_map:
                code, label = inst_map[sn]
                matched += 1
                if row["institution_code"] != code:
                    changed += 1
                updates.append((code, label, row["id"]))

        print(f"  Correspondências no DB: {matched}/{len(db_rows)} (Alterações de código: {changed})")

    # 2. Processar SUS-SP.pdf caso esteja no banco como OUTRO
    cur.execute("SELECT id FROM questions WHERE source_file = 'SUS-SP.pdf' AND (institution_code IS NULL OR institution_code = 'OUTRO')")
    sus_rows = cur.fetchall()
    for row in sus_rows:
        updates.append(("SUS-SP", "SUS-SP - Seleção Unificada para Residência Médica do Estado de São Paulo", row["id"]))
    if sus_rows:
        print(f"\nAtualizando {len(sus_rows)} questões de SUS-SP.pdf para 'SUS-SP'")

    # Executar atualizações
    print(f"\nAplicando {len(updates)} atualizações em lote no banco...")
    cur.executemany("UPDATE questions SET institution_code = ?, institution_label = ? WHERE id = ?", updates)
    conn.commit()

    print("\n--- DISTRIBUIÇÃO APÓS ATUALIZAÇÃO ---")
    cur.execute("SELECT institution_code, institution_label, COUNT(*) as cnt FROM questions GROUP BY institution_code, institution_label ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['institution_code']}: {r['cnt']} ({r['institution_label']})")

    print("\n--- DISTRIBUIÇÃO ESPECÍFICA DE SÍRIO, EINSTEIN E SCMSP ---")
    cur.execute("""
        SELECT source_file, institution_code, institution_label, COUNT(*) as cnt
        FROM questions 
        WHERE source_file LIKE '%SÍRIO%' OR source_file LIKE '%SIRIO%'
        GROUP BY source_file, institution_code, institution_label
        ORDER BY source_file, institution_code
    """)
    for r in cur.fetchall():
        print(f"  [{r['source_file']}] {r['institution_code']}: {r['cnt']} ({r['institution_label']})")

    conn.close()
    print("\nConcluído com sucesso!")


if __name__ == "__main__":
    run()
