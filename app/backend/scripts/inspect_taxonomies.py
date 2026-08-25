import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT DISTINCT area FROM questions WHERE area IS NOT NULL")
print("Areas:", [r[0] for r in c.fetchall()])

c.execute("SELECT DISTINCT topic FROM questions WHERE topic IS NOT NULL LIMIT 20")
print("Topics sample:", [r[0] for r in c.fetchall()])

conn.close()
