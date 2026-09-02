import os
import sys
import json
import urllib.request

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN são obrigatórios.")

req_body = {
    "requests": [
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM questions"}},
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM alternatives"}},
        {"type": "close"}
    ]
}

req = urllib.request.Request(
    TURSO_URL,
    data=json.dumps(req_body).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        q_count = data["results"][0]["response"]["result"]["rows"][0][0]["value"]
        alt_count = data["results"][1]["response"]["result"]["rows"][0][0]["value"]
        print(f"Status Atual no Turso:")
        print(f"  Questões: {q_count}")
        print(f"  Alternativas: {alt_count}")
except Exception as e:
    print("Erro:", e)
