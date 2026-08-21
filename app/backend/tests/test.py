import sqlite3

conn = sqlite3.connect('medquest.db')
try:
    print(conn.execute('SELECT snippet(questions_fts, 0, "[", "]", "...", 20) FROM questions_fts fts JOIN questions q ON q.id = fts.rowid WHERE questions_fts MATCH "trauma" LIMIT 1').fetchall())
except Exception as e:
    print('Error with questions_fts:', e)

try:
    print(conn.execute('SELECT snippet(fts, 0, "[", "]", "...", 20) FROM questions_fts fts JOIN questions q ON q.id = fts.rowid WHERE questions_fts MATCH "trauma" LIMIT 1').fetchall())
except Exception as e:
    print('Error with fts:', e)
