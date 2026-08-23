import sqlite3

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT subtema, COUNT(*) as count 
    FROM questions 
    WHERE area LIKE '%Preventiva%'
    GROUP BY subtema
    ORDER BY count DESC
""").fetchall()

print("Current Preventiva subtemas in DB:")
total = 0
for r in rows:
    total += r["count"]
    print(f" - {r['subtema']}: {r['count']} questions")

print(f"\nTotal Preventiva questions: {total}")
