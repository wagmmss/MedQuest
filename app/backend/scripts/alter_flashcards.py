import sqlite3


def upgrade_flashcards():
    conn = sqlite3.connect('medquest.db')
    cur = conn.cursor()
    columns = [row[1] for row in cur.execute("PRAGMA table_info(flashcards)").fetchall()]
    
    if "user_id" not in columns:
        cur.execute("ALTER TABLE flashcards ADD COLUMN user_id TEXT DEFAULT 'local'")
        print("Added user_id")
    if "source_context" not in columns:
        cur.execute("ALTER TABLE flashcards ADD COLUMN source_context TEXT")
        print("Added source_context")
    if "is_ai_generated" not in columns:
        cur.execute("ALTER TABLE flashcards ADD COLUMN is_ai_generated INTEGER DEFAULT 0")
        print("Added is_ai_generated")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_flashcards()
