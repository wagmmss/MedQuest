import sqlite3

DB_PATH = "c:/Users/wmors/OneDrive/Documentos/MedQuest/app/backend/medquest.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("--- VALIDANDO LIMPEZA ---")
cur.execute("SELECT COUNT(*) as cnt FROM questions WHERE missing_alts = 1")
print("missing_alts = 1:", cur.fetchone()['cnt'])

cur.execute("SELECT COUNT(*) as cnt FROM questions WHERE institution_code = 'instituição não identificada'")
print("instituição não identificada:", cur.fetchone()['cnt'])

print("\n--- VALIDANDO FTS5 ---")
try:
    cur.execute("SELECT COUNT(*) as cnt FROM questions_fts")
    print("Total records in questions_fts:", cur.fetchone()['cnt'])
    
    cur.execute("SELECT rowid, stem FROM questions_fts WHERE questions_fts MATCH 'paciente' LIMIT 3")
    print("\nBusca por 'paciente':")
    for row in cur.fetchall():
        print(f"ID: {row['rowid']} - Stem: {row['stem'][:60]}...")
except Exception as e:
    print("Erro FTS5:", e)

conn.close()
