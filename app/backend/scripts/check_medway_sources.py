import sqlite3, sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'c:\dev\MedQuest\app\backend\medquest.db')
c = conn.cursor()
# Ver todos os source_files de questões com institution_code = 'MEDWAY'
c.execute("SELECT source_file, COUNT(*) FROM questions WHERE institution_code='MEDWAY' GROUP BY source_file")
for r in c.fetchall():
    print(r)
conn.close()
