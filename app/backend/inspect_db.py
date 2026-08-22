import sqlite3
conn = sqlite3.connect('medquest.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions'")
print(cursor.fetchone()[0])
