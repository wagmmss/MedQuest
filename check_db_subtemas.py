import sqlite3

conn = sqlite3.connect('app/backend/medquest.db')
c = conn.cursor()

print("--- Craniossinostose in DB ---")
for row in c.execute("SELECT id, area, subtema, topic FROM questions WHERE stem LIKE '%craniossinostose%' OR stem LIKE '%cranioestenose%' OR topic LIKE '%Craniossinostose%'").fetchall():
    print(f"ID {row[0]}: Area='{row[1]}' | Subtema='{row[2]}' | Topic='{row[3]}'")

print("\n--- All distinct subtemas in Cirurgia in medquest.db ---")
for row in c.execute("SELECT DISTINCT subtema, COUNT(*) FROM questions WHERE area='Cirurgia' GROUP BY subtema").fetchall():
    print(f"{row[0]} ({row[1]} questions)")
