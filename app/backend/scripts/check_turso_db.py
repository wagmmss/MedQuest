import os
import sys
import io
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

print(f"TURSO_URL: {TURSO_URL}")
print(f"TURSO_TOKEN: {TURSO_TOKEN[:10]}..." if TURSO_TOKEN else "None")

if TURSO_URL and TURSO_TOKEN:
    import libsql
    client = libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    cur = client.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    print(f"Total de questões no TURSO: {total}")
    
    cur.execute("SELECT institution_code, COUNT(*) as cnt FROM questions GROUP BY institution_code ORDER BY cnt DESC")
    rows = cur.fetchall()
    print("\nInstituições no Turso:")
    for r in rows:
        print(f"  {r[0]}: {r[1]}")
else:
    print("Turso credentials not configured.")
