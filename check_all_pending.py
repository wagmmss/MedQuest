import sqlite3

conn = sqlite3.connect("app/backend/medquest.db")
c = conn.cursor()

c.execute("SELECT area, count(id) FROM questions WHERE id NOT IN (SELECT question_id FROM reclassification_audit) GROUP BY area")
rows = c.fetchall()
print("Questões pendentes por área:")
for r in rows:
    print(f"- {r[0]}: {r[1]}")

if not rows:
    print("Nenhuma questão pendente em nenhuma área!")

c.execute("SELECT count(id) FROM questions WHERE area = 'Clínica Médica'")
total_cm = c.fetchone()[0]

c.execute("SELECT count(DISTINCT question_id) FROM reclassification_audit WHERE new_area = 'Clínica Médica' OR old_area = 'Clínica Médica'")
audited_cm = c.fetchone()[0]

print(f"\nTotal de questões atualmente em Clínica Médica: {total_cm}")
print(f"Total de questões auditadas associadas à Clínica Médica: {audited_cm}")
