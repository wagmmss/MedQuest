import sqlite3

conn = sqlite3.connect('app/backend/medquest.db')
c = conn.cursor()
count = c.execute('SELECT COUNT(*) FROM questions WHERE area = "Cirurgia" AND id NOT IN (SELECT question_id FROM reclassification_audit)').fetchone()[0]
print(f"Remaining unaudited questions in Cirurgia: {count}")
