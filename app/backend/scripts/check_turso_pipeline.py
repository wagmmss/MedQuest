import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
env_vars = {}
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

# Also check root .env
root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
if os.path.exists(root_env):
    with open(root_env, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

TURSO_URL = env_vars.get("TURSO_DATABASE_URL")
TURSO_TOKEN = env_vars.get("TURSO_AUTH_TOKEN")

print(f"TURSO_URL: {TURSO_URL}")
print(f"TURSO_TOKEN: {TURSO_TOKEN[:10]}..." if TURSO_TOKEN else "None")

if TURSO_URL and TURSO_TOKEN:
    import urllib.request
    import json
    
    # Query Turso via HTTP API (pipeline endpoint)
    # Turso URL format: libsql://db-name.turso.io or https://db-name.turso.io
    http_url = TURSO_URL.replace("libsql://", "https://") + "/v2/pipeline"
    
    req_body = {
        "requests": [
            {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM questions"}},
            {"type": "execute", "stmt": {"sql": "SELECT institution_code, COUNT(*) as cnt FROM questions GROUP BY institution_code ORDER BY cnt DESC"}},
            {"type": "close"}
        ]
    }
    
    req = urllib.request.Request(
        http_url,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TURSO_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            total = data["results"][0]["response"]["result"]["rows"][0][0]["value"]
            print(f"\nTotal de questões no TURSO (Nuvem): {total}")
            print("\nInstituições no Turso (Nuvem):")
            for r in data["results"][1]["response"]["result"]["rows"]:
                inst = r[0]["value"] if "value" in r[0] else None
                cnt = r[1]["value"] if "value" in r[1] else 0
                print(f"  {inst}: {cnt}")
    except Exception as e:
        print("Erro ao consultar Turso:", e)
