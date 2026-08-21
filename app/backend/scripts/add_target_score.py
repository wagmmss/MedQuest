import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "medquest.db")

def add_columns():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE planner_config ADD COLUMN target_score REAL")
        print("Column target_score added to planner_config table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError target_score: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
