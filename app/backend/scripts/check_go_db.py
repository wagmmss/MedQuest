import sqlite3
import json

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT subtema, COUNT(*) as count 
    FROM questions 
    WHERE area LIKE '%Ginecologia%' OR area LIKE '%Obstetr%'
    GROUP BY subtema
    ORDER BY count DESC
""").fetchall()

print("Current Ginecologia e Obstetrícia Subtemas in DB:")
total_q = 0
for r in rows:
    total_q += r["count"]
    print(f" - {r['subtema']}: {r['count']} questions")

print(f"\nTotal GO questions in DB: {total_q}")
