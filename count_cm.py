import sqlite3

conn = sqlite3.connect("app/backend/medquest.db")
c = conn.cursor()
c.execute("SELECT count(id) FROM questions WHERE id NOT IN (SELECT question_id FROM reclassification_audit) AND area = 'Clínica Médica'")
total = c.fetchone()[0]
print(f"Total de questões pendentes em Clínica Médica: {total}")
