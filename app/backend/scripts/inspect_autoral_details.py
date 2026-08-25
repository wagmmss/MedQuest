import sqlite3

backup_path = r"C:\dev\MedQuest\app\backend\medquest.db.backup_images_20260824_220955"
conn = sqlite3.connect(backup_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

for sfile in ["USP-SP 2026 AUTORAL", "USP-RP 2026 AUTORAL", "UNIFESP 2026 AUTORAL"]:
    c.execute("""
        SELECT q.id, q.source_file, q.source_number, q.institution_code, q.editorial_status, 
               substr(q.stem, 1, 60) as stem_pre,
               count(a.id) as alt_cnt,
               e.explanation_text IS NOT NULL as has_exp
        FROM questions q
        LEFT JOIN alternatives a ON q.id = a.question_id
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.source_file = ?
        GROUP BY q.id
        LIMIT 2
    """, (sfile,))
    print(f"\n--- {sfile} ---")
    for r in c.fetchall():
        print(f"ID={r['id']} | Num={r['source_number']} | Alts={r['alt_cnt']} | Exp={r['has_exp']} | {r['stem_pre']}...")

conn.close()
