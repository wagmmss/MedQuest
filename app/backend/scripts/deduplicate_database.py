"""
Script de Desduplicação Segura do MedQuest.
Migra o histórico do usuário (tentativas, revisões espaçadas, flashcards e favoritos)
das questões legadas duplicadas para as questões canônicas oficiais dos cadernos completos,
e em seguida remove as duplicatas do banco, preservando questões legadas que sejam 100% únicas.
"""
import os
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
BACKUPS_DIR = os.path.join(os.path.dirname(os.path.dirname(BACKEND_DIR)), "backups")

OFFICIAL_FILES = [
    "SÍRIO EINSTEIN E SCMSP 2020 A 2023",
    "SÍRIO EINSTEIN E SCMSP 2024 A 2026",
    "UNIFESP E UNICAMP 2020 A 2022",
    "UNIFESP E UNICAMP 2023 A 2026",
    "USP 2020 a 2023",
    "USP 2024 a 2026"
]

LEGACY_FILES = [
    "Cirurgia",
    "Clínica Médica",
    "Miscelânea",
    "UNICAMP/UNIFESP",
    "SUS-SP.pdf"
]

def normalize_text(text):
    if not text:
        return ""
    v = unicodedata.normalize("NFKC", text).casefold()
    v = "".join(" " if unicodedata.category(c).startswith("P") else c for c in v)
    return re.sub(r"\s+", " ", v).strip()

def run():
    # 1. Backup de segurança
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_file = os.path.join(BACKUPS_DIR, f"medquest-pre-dedup-{ts}.db")
    shutil.copy2(DB_PATH, backup_file)
    print(f"Backup de segurança criado: {backup_file}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON")

    print("\n--- AUDITORIA ANTES DA DESDUPLICAÇÃO ---")
    cur.execute("SELECT COUNT(*) as total FROM questions")
    total_before = cur.fetchone()["total"]
    print(f"Total de questões: {total_before}")

    cur.execute("SELECT source_file, COUNT(*) as cnt FROM questions GROUP BY source_file ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['source_file']}: {r['cnt']}")

    # 2. Carregar questões oficiais
    placeholders = ",".join("?" * len(OFFICIAL_FILES))
    cur.execute(f"SELECT id, source_file, comment_code, stem FROM questions WHERE source_file IN ({placeholders})", OFFICIAL_FILES)
    official_rows = cur.fetchall()

    official_by_comment = {}
    official_by_stem = {}
    for r in official_rows:
        if r["comment_code"] and r["comment_code"].strip():
            official_by_comment[r["comment_code"].strip()] = r["id"]
        norm_s = normalize_text(r["stem"])
        if norm_s:
            official_by_stem[norm_s] = r["id"]

    # 3. Mapear questões legadas para as canônicas
    legacy_placeholders = ",".join("?" * len(LEGACY_FILES))
    cur.execute(f"SELECT id, source_file, comment_code, stem FROM questions WHERE source_file IN ({legacy_placeholders})", LEGACY_FILES)
    legacy_rows = cur.fetchall()

    legacy_to_canonical = {}
    unmatched_legacy = []

    for r in legacy_rows:
        canon_id = None
        c_code = (r["comment_code"] or "").strip()
        if c_code and c_code in official_by_comment:
            canon_id = official_by_comment[c_code]
        else:
            norm_s = normalize_text(r["stem"])
            if norm_s and norm_s in official_by_stem:
                canon_id = official_by_stem[norm_s]

        if canon_id:
            legacy_to_canonical[r["id"]] = canon_id
        else:
            unmatched_legacy.append(r["id"])

    print(f"\nQuestões legadas analisadas: {len(legacy_rows)}")
    print(f"  - Mapeadas para canônicas (duplicatas): {len(legacy_to_canonical)}")
    print(f"  - Únicas preservadas: {len(unmatched_legacy)}")

    # 4. Migração de dados de usuário e conteúdo em transação
    print("\nExecutando migração de dados do usuário...")
    with conn:
        migrated_attempts = 0
        migrated_srs = 0
        migrated_fc = 0
        migrated_fav = 0

        for legacy_id, canon_id in legacy_to_canonical.items():
            # A) Attempts
            cur.execute("SELECT id, user_id FROM attempts WHERE question_id = ?", (legacy_id,))
            attempts = cur.fetchall()
            for att in attempts:
                cur.execute("UPDATE attempts SET question_id = ? WHERE id = ?", (canon_id, att["id"]))
                migrated_attempts += 1

            # B) Spaced Repetition (PRIMARY KEY (question_id, user_id))
            cur.execute("SELECT user_id, efactor, interval, next_review_date, fsrs_card FROM spaced_repetition WHERE question_id = ?", (legacy_id,))
            srs_rows = cur.fetchall()
            for s in srs_rows:
                # Verificar se o usuário já tem registro no canon_id
                cur.execute("SELECT next_review_date FROM spaced_repetition WHERE question_id = ? AND user_id = ?", (canon_id, s["user_id"]))
                existing = cur.fetchone()
                if not existing:
                    cur.execute("""
                        INSERT INTO spaced_repetition (question_id, user_id, efactor, interval, next_review_date, fsrs_card)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (canon_id, s["user_id"], s["efactor"], s["interval"], s["next_review_date"], s["fsrs_card"]))
                    migrated_srs += 1
                # Remover do legacy
                cur.execute("DELETE FROM spaced_repetition WHERE question_id = ? AND user_id = ?", (legacy_id, s["user_id"]))

            # C) Favorites (PRIMARY KEY (question_id, user_id))
            cur.execute("SELECT user_id FROM favorites WHERE question_id = ?", (legacy_id,))
            fav_rows = cur.fetchall()
            for f in fav_rows:
                cur.execute("INSERT OR IGNORE INTO favorites (question_id, user_id) VALUES (?, ?)", (canon_id, f["user_id"]))
                cur.execute("DELETE FROM favorites WHERE question_id = ? AND user_id = ?", (legacy_id, f["user_id"]))
                migrated_fav += 1

            # D) Flashcards
            cur.execute("UPDATE flashcards SET question_id = ? WHERE question_id = ?", (canon_id, legacy_id))
            if cur.rowcount > 0:
                migrated_fc += cur.rowcount

            # E) Explanations (se o canônico não tiver e o legado tiver)
            cur.execute("SELECT explanation_text, generated_at FROM explanations WHERE question_id = ?", (legacy_id,))
            leg_exp = cur.fetchone()
            if leg_exp:
                cur.execute("SELECT question_id FROM explanations WHERE question_id = ?", (canon_id,))
                if not cur.fetchone():
                    cur.execute("INSERT INTO explanations (question_id, explanation_text, generated_at) VALUES (?, ?, ?)",
                                (canon_id, leg_exp["explanation_text"], leg_exp["generated_at"]))
                cur.execute("DELETE FROM explanations WHERE question_id = ?", (legacy_id,))

            # F) Question Images (se o canônico não tiver imagens e o legado tiver)
            cur.execute("SELECT file_path, order_index FROM question_images WHERE question_id = ?", (legacy_id,))
            leg_imgs = cur.fetchall()
            if leg_imgs:
                cur.execute("SELECT COUNT(*) as cnt FROM question_images WHERE question_id = ?", (canon_id,))
                if cur.fetchone()["cnt"] == 0:
                    for img in leg_imgs:
                        cur.execute("INSERT INTO question_images (question_id, file_path, order_index) VALUES (?, ?, ?)",
                                    (canon_id, img["file_path"], img["order_index"]))
                cur.execute("DELETE FROM question_images WHERE question_id = ?", (legacy_id,))

            # G) Alternatives do legado
            cur.execute("DELETE FROM alternatives WHERE question_id = ?", (legacy_id,))

            # H) Deletar questão legada duplicada
            cur.execute("DELETE FROM questions WHERE id = ?", (legacy_id,))

    print(f"  - Tentativas migradas: {migrated_attempts}")
    print(f"  - SRS migrados: {migrated_srs}")
    print(f"  - Flashcards migrados: {migrated_fc}")
    print(f"  - Favoritos migrados: {migrated_fav}")

    # 5. Otimizar e compactar banco
    print("\nExecutando verificação de integridade e VACUUM...")
    cur.execute("PRAGMA foreign_key_check")
    fk_errors = cur.fetchall()
    if fk_errors:
        print(f"AVISO: {len(fk_errors)} inconsistências de FK encontradas!")
    else:
        print("Integridade de chaves estrangeiras: 100% OK")

    conn.execute("VACUUM")

    # 6. Auditoria pós-desduplicação
    print("\n--- DISTRIBUIÇÃO APÓS DESDUPLICAÇÃO ---")
    cur.execute("SELECT COUNT(*) as total FROM questions")
    total_after = cur.fetchone()["total"]
    print(f"Total de questões: {total_after} (Removidas {total_before - total_after} duplicatas)")

    print("\nPor Instituição:")
    cur.execute("SELECT institution_code, institution_label, COUNT(*) as cnt FROM questions GROUP BY institution_code, institution_label ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['institution_code']}: {r['cnt']} ({r['institution_label']})")

    print("\nPor Origem:")
    cur.execute("SELECT source_file, COUNT(*) as cnt FROM questions GROUP BY source_file ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['source_file']}: {r['cnt']}")

    conn.close()
    print("\nDesduplicação segura concluída com sucesso!")


if __name__ == "__main__":
    run()
