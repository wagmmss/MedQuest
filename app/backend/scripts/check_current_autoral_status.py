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
    SELECT 
        institution_code,
        year,
        source_file,
        editorial_status,
        COUNT(*) as cnt
    FROM questions
    WHERE institution_code IN ('USP-SP', 'USP-RP', 'UNIFESP')
    GROUP BY institution_code, year, source_file, editorial_status
    ORDER BY institution_code, year DESC, source_file
""")

rows = c.fetchall()
print("=" * 80)
print(f"{'INST':<10} | {'YEAR':<5} | {'EDITORIAL':<10} | {'COUNT':<5} | {'SOURCE_FILE'}")
print("=" * 80)
for r in rows:
    ed = r['editorial_status'] or 'reviewed'
    print(f"{r['institution_code']:<10} | {r['year']:<5} | {ed:<10} | {r['cnt']:<5} | {r['source_file']}")
print("=" * 80)

conn.close()
