import sqlite3

conn = sqlite3.connect('medquest.db')
areas = ["Cirurgia", "Clínica Médica", "Pediatria", "Ginecologia e Obstetrícia", "Medicina Preventiva e Social"]
total = 0
for area in areas:
    c = conn.execute("SELECT COUNT(*) FROM questions q WHERE q.institution_code IN ('USP-SP', 'USP-RP') AND q.area = ? AND q.missing_alts = 0", (area,)).fetchone()[0]
    total += c
    print(area, c)
print("Total", total)
