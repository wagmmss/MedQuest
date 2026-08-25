import sqlite3
import os
import sys
import json

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Inspect table schemas
for tbl in ["questions", "alternatives", "explanations", "question_images"]:
    cursor.execute(f"PRAGMA table_info({tbl})")
    cols = [(r['name'], r['type'], r['notnull'], r['dflt_value'], r['pk']) for r in cursor.fetchall()]
    print(f"\n--- Tabela {tbl} ---")
    for c in cols:
        print(f"  {c[0]}: {c[1]} (pk={c[4]})")

# 2. Check current USP-SP 2026 questions
cursor.execute("""
    SELECT id, source_file, source_number, year, institution_code, institution_label,
           substr(stem, 1, 60) as stem_preview, correct_letter
    FROM questions
    WHERE institution_code = 'USP-SP' AND year = 2026
""")
rows = cursor.fetchall()
print(f"\nTotal USP-SP 2026 no banco atual: {len(rows)}")
for r in rows[:5]:
    print(f"ID={r['id']} | Num={r['source_number']} | Gab={r['correct_letter']} | {r['stem_preview']}...")

conn.close()
