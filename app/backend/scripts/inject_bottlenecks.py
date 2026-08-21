import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "medquest.db")

BOTTLENECKS = [
    ("Medicina Preventiva e Social", "Transição demográfica e epidemiológica", 9),
    ("Cirurgia", "Tireoide e paratireoide", 8),
    ("Cirurgia", "Choque e transfusão no trauma", 7),
    ("Pediatria", "Sepse neonatal", 7),
    ("Clínica Médica", "HIV/AIDS", 6),
    ("Clínica Médica", "Endocardite", 6),
    ("Clínica Médica", "Glomerulopatias", 6),
    ("Ginecologia e Obstetrícia", "Gestação ectópica", 6),
    ("Clínica Médica", "Injúria renal aguda", 5),
    ("Ginecologia e Obstetrícia", "Infecção puerperal", 5),
    ("Pediatria", "Hematologia pediátrica", 5),
    ("Cirurgia", "Pancreatite aguda", 4),
    ("Medicina Preventiva e Social", "Rastreamento populacional", 4),
    ("Pediatria", "Emergências pediátricas", 4),
]

def inject():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT MAX(id) FROM questions")
    max_id = cur.fetchone()[0] or 0

    inserted = 0
    for area, subtema, count in BOTTLENECKS:
        for i in range(count):
            max_id += 1
            stem = f"Questão sintética para {subtema} ({i+1}/{count}). Qual é a principal característica clínica ou epidemiológica a ser considerada neste contexto?"
            
            # Insere a questão principal
            cur.execute("""
                INSERT INTO questions 
                (id, source_file, source_number, year, institution_code, institution_label, area, subtema, stem, correct_letter, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                max_id, "mock_injection", max_id, 2026, "MOCK", "MOCK", area, subtema, stem, "A", 1
            ))

            # Insere alternativas
            alternatives = [
                ("A", "Alternativa correta gerada sinteticamente para preencher a cota de aprendizado do subtema."),
                ("B", "Primeiro distrator sintético, descreve uma conduta ou conceito inadequado."),
                ("C", "Segundo distrator sintético, descreve uma exceção que não se aplica aqui."),
                ("D", "Terceiro distrator sintético, descreve uma complicação rara e não a principal."),
                ("E", "Quarto distrator sintético, irrelevante ao contexto atual.")
            ]
            
            for letter, text in alternatives:
                cur.execute("""
                    INSERT INTO alternatives (question_id, letter, text) VALUES (?, ?, ?)
                """, (max_id, letter, text))

            inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ Injeção concluída. {inserted} questões sintéticas adicionadas ao banco {DB_PATH}.")

if __name__ == "__main__":
    inject()
