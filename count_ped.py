import sqlite3

conn = sqlite3.connect('app/backend/medquest.db')
c = conn.cursor()
c.execute("""
    SELECT area, COUNT(*) 
    FROM questions 
    WHERE id NOT IN (SELECT question_id FROM reclassification_audit)
    GROUP BY area
""")
for row in c.fetchall():
    print(f"{row[0]}: {row[1]} pendentes")
