import sqlite3
import json
conn = sqlite3.connect('medquest.db')
rows = conn.execute("SELECT DISTINCT institution_code FROM questions").fetchall()
print([r[0] for r in rows])
