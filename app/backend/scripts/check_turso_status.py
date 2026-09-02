import os
import requests
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
if not TURSO_URL or not TURSO_TOKEN:
    raise SystemExit("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN são obrigatórios.")
PIPELINE_URL = f"{TURSO_URL}/v3/pipeline"
HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json",
}

def make_execute(sql, args=None):
    stmt = {"sql": sql}
    if args:
        stmt["args"] = args
    return {"type": "execute", "stmt": stmt}

def make_close():
    return {"type": "close"}

def execute_pipeline(requests_list):
    resp = requests.post(PIPELINE_URL, headers=HEADERS, json={"requests": requests_list}, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"HTTP {resp.status_code}: {resp.text}")

print("Consultando Turso Cloud...")
res = execute_pipeline([
    make_execute("SELECT COUNT(*) FROM questions WHERE source_file = 'USP-RP 2026 AUTORAL'"),
    make_execute("SELECT COUNT(*) FROM alternatives WHERE question_id IN (SELECT id FROM questions WHERE source_file = 'USP-RP 2026 AUTORAL')"),
    make_execute("SELECT COUNT(*) FROM explanations WHERE question_id IN (SELECT id FROM questions WHERE source_file = 'USP-RP 2026 AUTORAL')"),
    make_execute("SELECT COUNT(*) FROM questions WHERE institution_code = 'USP-RP'"),
    make_close()
])

results = res.get("results", [])
q_cnt = results[0]["response"]["result"]["rows"][0][0]["value"]
alt_cnt = results[1]["response"]["result"]["rows"][0][0]["value"]
exp_cnt = results[2]["response"]["result"]["rows"][0][0]["value"]
usprp_total = results[3]["response"]["result"]["rows"][0][0]["value"]

print(f"Resultado no Turso Cloud:")
print(f"- Questões USP-RP 2026 AUTORAL: {q_cnt} / 100")
print(f"- Alternativas USP-RP 2026 AUTORAL: {alt_cnt} / 400")
print(f"- Explicações USP-RP 2026 AUTORAL: {exp_cnt} / 100")
print(f"- Total acumulado da USP-RP no Turso: {usprp_total} questões")
