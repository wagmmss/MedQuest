import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("SELECT id, area, subtema, topic, stem FROM questions").fetchall()

# Specific targeted classifications for surgery sub-specialties
cir_updates = []
for q in questions:
    if q["area"] == "Cirurgia":
        text = (str(q["topic"]) + " " + str(q["stem"])).lower()
        sub = q["subtema"]
        
        # Fraturas Ósseas
        if re.search(r"\bfratura\b|consolidação óssea|osteossíntese|rádio distal|colo do fêmur|tíbia|diáfise", text) and "exposta" not in text and "face" not in text and "tce" not in text and "coluna" not in text:
            cir_updates.append(("Fraturas Ósseas", q["id"]))
        # Cólon e Reto na cirurgia
        elif re.search(r"câncer colorretal|câncer de reto|câncer de cólon|colectomia|reto sigmoide|hemorroida|fissura anal|abscesso anorretal|fístula anal", text):
            cir_updates.append(("Cólon e Reto na cirurgia", q["id"]))
        # Cirurgia Torácica
        elif re.search(r"derrames pleurais|empiema pleural|pleuroscopia|toracotomia|simpatectomia|hiperidrose", text):
            cir_updates.append(("Cirurgia Torácica", q["id"]))
        # Polipose intestinal
        elif re.search(r"polipose|pólipos adenomatosos|paf\b|síndrome de peutz-jeghers", text):
            cir_updates.append(("Polipose intestinal", q["id"]))
        # Tendinites/Bursites
        elif re.search(r"tendinite|bursite|fasceíte plantar|epicondilite|tenossinovite|manguito rotador", text):
            cir_updates.append(("Tendinites/ Tenossinovites/ Fasceítes e Bursites", q["id"]))
        # Ortopedia Pediátrica
        elif re.search(r"displasia do quadril|pé torto congênito|epifisiólise|doença de legg-calvé-perthes", text):
            cir_updates.append(("Ortopedia Pediátrica", q["id"]))
        # Tumores Ortopédicos
        elif re.search(r"osteossarcoma|sarcoma de ewing|condrossarcoma|tumor de células gigantes", text):
            cir_updates.append(("Tumores Ortopédicos", q["id"]))

print(f"Found {len(cir_updates)} surgical targeted updates!")
if cir_updates:
    conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", cir_updates)
    conn.commit()
    print("Applied surgical targeted updates!")
