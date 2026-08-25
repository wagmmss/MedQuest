import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'trigger')")
for name, mtype, sql in c.fetchall():
    if not name.startswith("sqlite_"):
        print(f"[{mtype.upper()}] {name}")
        if sql:
            print(sql[:250] + "...")
        print("-" * 50)
conn.close()
