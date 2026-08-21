import sqlite3

conn = sqlite3.connect('medquest.db')
columns = [row[1] for row in conn.execute("PRAGMA table_info(flashcards)").fetchall()]
print("Flashcards columns:", columns)
