import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT year, source_file, count(*) as cnt, min(source_number) as min_num, max(source_number) as max_num
    FROM questions
    WHERE institution_code = 'UNICAMP'
    GROUP BY year, source_file
    ORDER BY year DESC
""")
print("Status atual de UNICAMP:")
for r in c.fetchall():
    print(f"  Ano {r['year']}: {r['cnt']} questoes ({r['source_file']}) -> Nums {r['min_num']}..{r['max_num']}")

conn.close()
