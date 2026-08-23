import sqlite3
import json

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT subtema, topic, COUNT(*) as count 
    FROM questions 
    WHERE area LIKE '%Ginecologia%' OR area LIKE '%Obstetr%'
    GROUP BY subtema, topic
    ORDER BY subtema, count DESC
""").fetchall()

print(f"Total topic groups: {len(rows)}")
current_sub = None
for r in rows:
    if r["subtema"] != current_sub:
        current_sub = r["subtema"]
        print(f"\n[{current_sub}]")
    print(f"   - {r['topic']}: {r['count']} questions")
