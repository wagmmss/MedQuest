import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("app/backend/medquest.db")
c = conn.cursor()

print("=== DISTRIBUIÇÃO ATUAL DE PEDIATRIA NO BANCO ===")
c.execute("""
    SELECT subtema, COUNT(*) 
    FROM questions 
    WHERE area = 'Pediatria'
    GROUP BY subtema 
    ORDER BY COUNT(*) DESC
""")
total_ped = 0
for row in c.fetchall():
    print(f" - {row[0]}: {row[1]}")
    total_ped += row[1]
print(f"Total em Pediatria: {total_ped}")

print("\n=== TOTAL AUDITADO EM PEDIATRIA ===")
c.execute("""
    SELECT COUNT(*) 
    FROM reclassification_audit 
    WHERE old_area = 'Pediatria' OR new_area = 'Pediatria'
""")
print(f"Registros de auditoria envolvendo Pediatria: {c.fetchone()[0]}")
