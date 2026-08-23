import sqlite3
import sys

conn = sqlite3.connect('app/backend/medquest.db')
c = conn.cursor()

def search_kw(kw):
    print(f"=== SEARCH: {kw} ===")
    rows = c.execute("SELECT id, area, subtema, topic FROM questions WHERE lower(stem) LIKE ? OR lower(topic) LIKE ? LIMIT 10", (f"%{kw.lower()}%", f"%{kw.lower()}%")).fetchall()
    for r in rows:
        print(f"ID {r[0]}: [{r[1]} -> {r[2]}] (Topic: {r[3]})")

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        search_kw(arg)
