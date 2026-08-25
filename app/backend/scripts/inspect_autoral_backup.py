import sqlite3
import os

backup_path = r"C:\dev\MedQuest\app\backend\medquest.db.backup_images_20260824_220955"
if os.path.exists(backup_path):
    conn = sqlite3.connect(backup_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT source_file, institution_code, institution_label, year, editorial_status, COUNT(*) as cnt
        FROM questions
        WHERE source_file LIKE '%AUTORAL%' OR editorial_status = 'autoral'
        GROUP BY source_file, institution_code, institution_label, year, editorial_status
    """)
    print("Lotes AUTORAIS encontrados no backup anterior:")
    for r in c.fetchall():
        print(f"  {r['source_file']} | {r['institution_code']} | {r['year']} | editorial_status={r['editorial_status']} -> {r['cnt']} questoes")
    conn.close()
else:
    print("Backup nao encontrado:", backup_path)
