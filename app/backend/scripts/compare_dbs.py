import sqlite3
import os

db1 = r"c:\dev\MedQuest\app\backend\medquest.db"
db2 = r"c:\dev\MedQuest\app\backend\scripts\medquest.db"
db3 = r"c:\dev\MedQuest\medquest.db"

for p in [db1, db2, db3]:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM questions")
        total = c.fetchone()[0]
        size_mb = os.path.getsize(p) / (1024 * 1024)
        print(f"DB: {p} (Tamanho: {size_mb:.2f} MB)")
        print(f"  Total de questões: {total}")
        c.execute("SELECT institution_code, COUNT(*) FROM questions GROUP BY institution_code ORDER BY COUNT(*) DESC")
        for inst, cnt in c.fetchall()[:10]:
            print(f"    {inst}: {cnt}")
        conn.close()
