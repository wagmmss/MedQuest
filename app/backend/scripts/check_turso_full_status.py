import json
import urllib.request
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN são obrigatórios.")

req_body = {
    "requests": [
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM questions"}},
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM alternatives"}},
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM explanations"}},
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM question_images"}},
        {"type": "execute", "stmt": {"sql": "SELECT institution_code, COUNT(*) as cnt FROM questions GROUP BY institution_code ORDER BY cnt DESC"}},
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
        exp_count = data["results"][2]["response"]["result"]["rows"][0][0]["value"]
        img_count = data["results"][3]["response"]["result"]["rows"][0][0]["value"]
        print(f"📊 Relatório Turso Cloud:")
        print(f"  Questões: {q_count}")
        print(f"  Alternativas: {alt_count}")
        print(f"  Explicações: {exp_count}")
        print(f"  Imagens: {img_count}")
        print(f"\nContagem por Instituição:")
        for r in data["results"][4]["response"]["result"]["rows"]:
            print(f"  {r[0]['value']}: {r[1]['value']}")
except Exception as e:
    print("Erro:", e)
