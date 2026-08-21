import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "medquest.db")

def add_columns():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE flashcards ADD COLUMN is_ai_generated INTEGER DEFAULT 0")
        print("Column is_ai_generated added to flashcards table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError is_ai_generated: {e}")
        
    try:
        cur.execute("ALTER TABLE flashcards ADD COLUMN report_status TEXT")
        print("Column report_status added to flashcards table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError report_status: {e}")

    # check schema
    cur.execute("PRAGMA table_info(flashcards)")
    print(cur.fetchall())
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
