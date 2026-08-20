import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "medquest.db")

def add_column():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE questions ADD COLUMN medical_references TEXT")
        print("Column medical_references added to questions table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column()
