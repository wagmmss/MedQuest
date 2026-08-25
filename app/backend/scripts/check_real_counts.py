import sqlite3
import os
import json

db_path = r"c:\dev\MedQuest\app\backend\medquest.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT COUNT(*) as total FROM questions")
total = c.fetchone()["total"]

c.execute("SELECT institution_code, COUNT(*) as cnt FROM questions GROUP BY institution_code ORDER BY cnt DESC")
insts = c.fetchall()

print(f"Total REAL no banco medquest.db: {total}")
print("\nContagem REAL por instituição no banco medquest.db:")
for r in insts:
    print(f"  {r['institution_code']}: {r['cnt']}")
conn.close()
