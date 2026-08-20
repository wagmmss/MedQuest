import os
import sqlite3
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Adicionar novas colunas em questions
    cols = [r[1] for r in conn.execute("PRAGMA table_info(questions)")]
    
    new_cols = [
        ("subtema_id", "TEXT"),
        ("medical_references", "TEXT"),
        ("review_date", "TEXT"),
        ("editorial_status", "TEXT"),
        ("status", "TEXT DEFAULT 'active'")
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in cols:
            print(f"Adding column {col_name} to questions table...")
            try:
                conn.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
                
    # Update subtema to subtema_id
    map_path = os.path.join(BACKEND_DIR, "data", "subtema_map.json")
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            subtema_map = json.load(f)
            
        print("Migrating subtema strings to subtema_id...")
        changed = 0
        for subtema_name, subtema_id in subtema_map.items():
            cursor = conn.execute("UPDATE questions SET subtema_id = ? WHERE subtema = ?", (subtema_id, subtema_name))
            changed += cursor.rowcount
        print(f"Updated {changed} questions with subtema_id.")
    
    # Isolar questões incompletas
    print("Quarantining incomplete questions...")
    # 54 questions without alternatives, area or subtema
    cursor = conn.execute("""
        UPDATE questions 
        SET status = 'quarantined' 
        WHERE missing_alts = 1 OR area IS NULL OR subtema IS NULL OR area = '' OR subtema = ''
    """)
    print(f"Quarantined {cursor.rowcount} questions.")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
