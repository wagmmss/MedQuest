import sqlite3, sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'c:\dev\MedQuest\app\backend\medquest.db')
c = conn.cursor()
# Mostrar exemplos de questões de cada módulo para ver se tem banca no tópico/área
for src in [
    'MEDWAY MÓDULO LUXAÇÕES E LESÕES LIGAMENTARES 2026',
    'MEDWAY MÓDULO QUEIMADURAS PED 2026',
    'MEDWAY MÓDULO TRANSTORNOS POR USO DE SUBSTÂNCIAS 2026',
]:
    print(f"\n=== {src} ===")
    c.execute("SELECT id, topic, area, subtema, stem FROM questions WHERE source_file=? LIMIT 3", (src,))
    for r in c.fetchall():
        print(f"  ID={r[0]} | topic={r[1]} | area={r[2]} | subtema={r[3]}")
        print(f"  stem[:100]={r[4][:100]}")
conn.close()
