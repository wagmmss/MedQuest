"""
Adiciona um novo PDF exportado (ex: UNICAMP/UNIFESP) ao banco de dados EXISTENTE,
sem apagar nada (perguntas, explicações, tentativas já gravadas continuam intactas).

Uso:
    python extract_incremental.py <arquivo.pdf> <source_file_label> <slug_pasta_imagens>

Exemplo:
    python extract_incremental.py UNICAMP.pdf "UNICAMP/UNIFESP" unicampunifesp
"""
import hashlib
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract  # reaproveita parse_pdf, collect_image_candidates, filter_decorative_and_save, assign_images_to_questions

SRC_DIR = r"C:\Users\wmors\OneDrive\Documentos\MedQuest"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

DECORATIVE_REPEAT_THRESHOLD = 3


def main():
    pdf_fname = sys.argv[1]
    source_label = sys.argv[2]
    slug = sys.argv[3]

    path = os.path.join(SRC_DIR, pdf_fname)
    records, anchors = extract.parse_pdf(path, source_label)

    print("    coletando candidatas a imagem...")
    candidates = extract.collect_image_candidates(path)
    hash_counts = {}
    for c in candidates:
        h = hashlib.md5(c["data"]).hexdigest()
        hash_counts[h] = hash_counts.get(h, 0) + 1
    decorative_hashes = {h for h, n in hash_counts.items() if n > DECORATIVE_REPEAT_THRESHOLD}
    print(f"    {len(candidates)} candidatas, {len(decorative_hashes)} hashes decorativos excluídos")

    images = extract.filter_decorative_and_save(candidates, slug, decorative_hashes)
    image_map = extract.assign_images_to_questions(anchors, images)
    n_assigned = sum(len(v) for v in image_map.values())
    print(f"    {len(images)} imagens de conteúdo reais, {n_assigned} associadas a questões")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # evita duplicar se o script for rodado 2x para o mesmo arquivo
    existing = cur.execute(
        "SELECT COUNT(*) FROM questions WHERE source_file = ?", (source_label,)
    ).fetchone()[0]
    if existing:
        print(f"AVISO: já existem {existing} questões com source_file='{source_label}' no banco. Abortando para não duplicar.")
        conn.close()
        return

    n_inserted = 0
    for r in records:
        cur.execute(
            """INSERT INTO questions
            (source_file, source_number, year, institution_code, institution_label,
             topic, stem, correct_letter, missing_alts, comment_code, page_start, page_end)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_label, r["source_number"], r["year"], r["institution_code"],
             r["institution_label"], r["topic"], r["stem"], r["correct_letter"],
             1 if r["missing_alts"] else 0, r["comment_code"], r["page_start"], r["page_end"]),
        )
        qid = cur.lastrowid
        n_inserted += 1
        for letter, text in r["alternatives"].items():
            cur.execute(
                "INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?,?,?,?)",
                (qid, letter, text, 1 if letter == r["correct_letter"] else 0),
            )
        for order, fp in enumerate(image_map.get(r["source_number"], [])):
            cur.execute(
                "INSERT INTO question_images (question_id, file_path, order_index) VALUES (?,?,?)",
                (qid, fp, order),
            )

    conn.commit()

    missing_alts_n = sum(1 for r in records if r["missing_alts"])
    print(f"OK -> {n_inserted} questões inseridas ({missing_alts_n} com alternativas ausentes)")

    inst_counts = {}
    for r in records:
        inst_counts[r["institution_code"]] = inst_counts.get(r["institution_code"], 0) + 1
    print("Distribuição por instituição:", inst_counts)

    conn.close()


if __name__ == "__main__":
    main()
