import sqlite3
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

backup_path = r"C:\dev\MedQuest\app\backend\medquest.db.backup_images_20260824_220955"
current_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

print(f"Lendo lotes autorais do backup: {backup_path}")
print(f"Inserindo no banco atual: {current_path}")

b_conn = sqlite3.connect(backup_path)
b_conn.row_factory = sqlite3.Row
b_cur = b_conn.cursor()

c_conn = sqlite3.connect(current_path)
c_conn.row_factory = sqlite3.Row
c_cur = c_conn.cursor()

autoral_files = ["USP-SP 2026 AUTORAL", "USP-RP 2026 AUTORAL", "UNIFESP 2026 AUTORAL"]

# Check existing autorais in current db
c_cur.execute("SELECT source_file, count(*) FROM questions WHERE editorial_status = 'autoral' OR source_file LIKE '%AUTORAL%' GROUP BY source_file")
print("Lotes autorais presentes no banco atual antes da restauração:", c_cur.fetchall())

restored_total = 0

for sfile in autoral_files:
    b_cur.execute("SELECT * FROM questions WHERE source_file = ?", (sfile,))
    questions = b_cur.fetchall()
    print(f"\nProcessando {sfile}: {len(questions)} questões no backup...")

    # Delete any partial from current db first to avoid duplicate IDs
    c_cur.execute("SELECT id FROM questions WHERE source_file = ?", (sfile,))
    existing_ids = [r[0] for r in c_cur.fetchall()]
    if existing_ids:
        placeholders = ",".join("?" * len(existing_ids))
        c_cur.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", existing_ids)
        c_cur.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", existing_ids)
        c_cur.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", existing_ids)
        c_cur.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", existing_ids)

    for q in questions:
        old_id = q["id"]
        
        # Insert question
        c_cur.execute("""
            INSERT INTO questions (
                source_file, source_number, year, institution_code, institution_label,
                topic, stem, correct_letter, missing_alts, comment_code,
                page_start, page_end, area, subtema, subtema_orig, subtema_id,
                medical_references, review_date, editorial_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q["source_file"], q["source_number"], q["year"], q["institution_code"], q["institution_label"],
            q["topic"], q["stem"], q["correct_letter"], q["missing_alts"], q["comment_code"],
            q["page_start"], q["page_end"], q["area"], q["subtema"], q["subtema_orig"], q["subtema_id"],
            q["medical_references"], q["review_date"], "autoral", "active"
        ))
        new_q_id = c_cur.lastrowid

        # Alternatives
        b_cur.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ?", (old_id,))
        for alt in b_cur.fetchall():
            c_cur.execute("""
                INSERT INTO alternatives (question_id, letter, text, is_correct)
                VALUES (?, ?, ?, ?)
            """, (new_q_id, alt["letter"], alt["text"], alt["is_correct"]))

        # Explanation
        b_cur.execute("SELECT explanation_text, generated_at, reviewed_at FROM explanations WHERE question_id = ?", (old_id,))
        exp = b_cur.fetchone()
        if exp:
            c_cur.execute("""
                INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at)
                VALUES (?, ?, ?, ?)
            """, (new_q_id, exp["explanation_text"], exp["generated_at"], exp["reviewed_at"]))

        # Images
        b_cur.execute("SELECT file_path, order_index FROM question_images WHERE question_id = ?", (old_id,))
        for img in b_cur.fetchall():
            c_cur.execute("""
                INSERT INTO question_images (question_id, file_path, order_index)
                VALUES (?, ?, ?)
            """, (new_q_id, img["file_path"], img["order_index"]))

        restored_total += 1

c_conn.commit()
print(f"\n[SUCESSO] Restauradas com sucesso {restored_total} questões dos lotes autorais!")

b_conn.close()
c_conn.close()
