import sqlite3
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT institution_code, institution_label, year, COUNT(*) as cnt, source_file
    FROM questions
    GROUP BY institution_code, institution_label, year, source_file
    ORDER BY institution_code, year DESC
""")
rows = c.fetchall()

print("=" * 85)
print(f"{'INST_CODE':<12} | {'YEAR':<5} | {'COUNT':<5} | {'SOURCE_FILE':<25} | {'LABEL'}")
print("=" * 85)
for r in rows:
    print(f"{r['institution_code']:<12} | {r['year']:<5} | {r['cnt']:<5} | {r['source_file']:<25} | {r['institution_label'][:35]}")

print("=" * 85)
conn.close()
