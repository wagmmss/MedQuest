import sqlite3, sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'c:\dev\MedQuest\app\backend\medquest.db')
c = conn.cursor()
c.execute("SELECT institution_code, institution_label, source_file, COUNT(*) FROM questions WHERE editorial_status='autoral' GROUP BY institution_code ORDER BY COUNT(*) DESC")
for r in c.fetchall():
    print(r)
conn.close()
