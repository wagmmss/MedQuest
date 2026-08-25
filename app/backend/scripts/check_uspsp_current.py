import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT source_file, year, COUNT(*) as cnt 
    FROM questions 
    WHERE institution_code = 'USP-SP' 
    GROUP BY source_file, year
""")
print("Status atual de USP-SP no banco:")
for r in c.fetchall():
    print(f"  {r['source_file']} ({r['year']}): {r['cnt']} questoes")

c.execute("""
    SELECT COUNT(*) as total 
    FROM questions 
    WHERE institution_code = 'USP-SP'
""")
total = c.fetchone()['total']
print(f"TOTAL USP-SP: {total} questoes")

conn.close()
