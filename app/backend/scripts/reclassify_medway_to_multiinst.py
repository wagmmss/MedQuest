"""
Reclassifica as questões autorais da Medway com institution_code='MEDWAY'
para institution_code='MULTIINST' (módulos temáticos multi-banca).
Também atualiza o Turso Cloud via HTTP pipeline.
"""
import sqlite3
import sys
import io
import json
import urllib.request
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"c:\dev\MedQuest\app\backend\medquest.db"
TURSO_URL = "https://medquest-wagmss.aws-us-east-1.turso.io/v2/pipeline"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODYyMjYzMjUsImlkIjoiMDE5ZmUzNjItNmUwMS03YTE5LTkyZjctMGRhOTJlZTk5OWQ0Iiwia2lkIjoiTlhsOWVXamdJaXcwVW5vNmhSTGdhSVFsRl9OaVBxSm13eHB6U21hY1hNUSIsInJpZCI6IjJhMjVkMzQ0LWI3ZTctNDA5YS1hMmIzLTVlNWNkMTgxMWE4NCJ9.jOZcgW1n4dCGN1W8SPG-vMFpj734oh0Wn1NDl7lteH6NsD5nqeOXmr1tZm4TEQVhTO-_2aN29LBz1u7o29D1Dw"

NEW_CODE  = "MULTIINST"
NEW_LABEL = "Multi-Institucional (Módulos Temáticos)"

def turso_pipeline(requests_list):
    payload = json.dumps({"requests": requests_list}).encode("utf-8")
    req = urllib.request.Request(TURSO_URL, data=payload, headers={
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

# --- 1. Atualizar banco LOCAL ---
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Quantas questões vão mudar?
c.execute("SELECT COUNT(*) FROM questions WHERE institution_code='MEDWAY'")
total = c.fetchone()[0]
print(f"Questões com institution_code='MEDWAY' no banco local: {total}")

# Atualizar
c.execute("""
    UPDATE questions
    SET institution_code = ?,
        institution_label = ?
    WHERE institution_code = 'MEDWAY'
""", (NEW_CODE, NEW_LABEL))
conn.commit()

c.execute("SELECT COUNT(*) FROM questions WHERE institution_code=?", (NEW_CODE,))
updated = c.fetchone()[0]
print(f"[LOCAL] Atualizadas para '{NEW_CODE}': {updated} questões")

# Confirmar que não sobrou nenhuma 'MEDWAY'
c.execute("SELECT COUNT(*) FROM questions WHERE institution_code='MEDWAY'")
remaining = c.fetchone()[0]
print(f"[LOCAL] Questões com 'MEDWAY' restantes: {remaining}")

conn.close()

# --- 2. Atualizar banco TURSO CLOUD ---
print(f"\nAtualizando Turso Cloud...")
result = turso_pipeline([
    {"type": "execute", "stmt": {
        "sql": "UPDATE questions SET institution_code = ?, institution_label = ? WHERE institution_code = 'MEDWAY'",
        "args": [
            {"type": "text", "value": NEW_CODE},
            {"type": "text", "value": NEW_LABEL}
        ]
    }},
    {"type": "close"}
])

# Verificar resultado
turso_ok = any(r.get("type") == "ok" for r in result.get("results", []))
if turso_ok:
    print(f"[TURSO] Questões MEDWAY -> {NEW_CODE} atualizadas com sucesso!")
else:
    print(f"[TURSO] Resultado:", result)

# --- 3. Verificar no Turso ---
verify = turso_pipeline([
    {"type": "execute", "stmt": {"sql": "SELECT institution_code, COUNT(*) FROM questions WHERE institution_code IN ('MEDWAY','MULTIINST') GROUP BY institution_code"}},
    {"type": "close"}
])
rows = verify["results"][0]["response"]["result"]["rows"]
print(f"\n[TURSO] Contagem final por código:")
for r in rows:
    print(f"  {r[0]['value']}: {r[1]['value']}")
if not rows:
    print("  Nenhuma questão 'MEDWAY' ou 'MULTIINST' (algo deu errado)")

print(f"\nDone! A banca 'MEDWAY' foi renomeada para '{NEW_CODE}' ({NEW_LABEL}).")
