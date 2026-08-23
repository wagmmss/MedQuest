import sqlite3

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT area, COUNT(*) as count FROM questions GROUP BY area").fetchall()
print("Distinct areas in medquest.db:")
for r in rows:
    print(f" - '{r['area']}': {r['count']} questions")
