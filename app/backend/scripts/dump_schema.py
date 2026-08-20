import sqlite3
import os

db_path = "c:/Users/wmors/OneDrive/Documentos/MedQuest/app/backend/medquest.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("--- SCHEMA ---")
cur = conn.cursor()
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
for row in cur.fetchall():
    print(row['sql'])

print("\n--- MISSING INSTITUTIONS ---")
cur.execute("SELECT COUNT(*) as cnt FROM questions WHERE institution_code IS NULL OR institution_code = 'instituição não identificada' OR institution_label LIKE '%não identificada%'")
print("Missing institutions count:", cur.fetchone()['cnt'])

print("\n--- MISSING ALTS ---")
cur.execute("SELECT COUNT(*) as cnt FROM questions WHERE missing_alts = 1")
print("Questions with missing_alts = 1:", cur.fetchone()['cnt'])

conn.close()
