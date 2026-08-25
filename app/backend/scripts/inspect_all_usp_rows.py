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
    SELECT source_file, institution_code, institution_label, year, COUNT(*) as cnt,
           MIN(id) as min_id, MAX(id) as max_id
    FROM questions
    WHERE institution_code LIKE '%USP%' 
       OR institution_label LIKE '%USP%' 
       OR source_file LIKE '%USP%'
    GROUP BY source_file, institution_code, institution_label, year
    ORDER BY year DESC, institution_code, source_file
""")

rows = c.fetchall()
print("=" * 80)
print(" TODAS AS QUESTÕES RELACIONADAS À USP NO BANCO:")
print("=" * 80)
for r in rows:
    print(f"Ano: {r['year']} | Cod: {r['institution_code']} | Label: {r['institution_label'][:40]} | Source: {r['source_file']} -> {r['cnt']} questoes (IDs {r['min_id']}..{r['max_id']})")

conn.close()
