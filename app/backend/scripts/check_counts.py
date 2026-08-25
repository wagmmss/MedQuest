import os
import requests
import json
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "libsql://medquest-wagmss.aws-us-east-1.turso.io").replace("libsql://", "https://").replace("wss://", "https://")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN") or "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODYyMjYzMjUsImlkIjoiMDE5ZmUzNjItNmUwMS03YTE5LTkyZjctMGRhOTJlZTk5OWQ0Iiwia2lkIjoiTlhsOWVXamdJaXcwVW5vNmhSTGdhSVFsRl9OaVBxSm13eHB6U21hY1hNUSIsInJpZCI6IjJhMjVkMzQ0LWI3ZTctNDA5YS1hMmIzLTVlNWNkMTgxMWE4NCJ9.jOZcgW1n4dCGN1W8SPG-vMFpj734oh0Wn1NDl7lteH6NsD5nqeOXmr1tZm4TEQVhTO-_2aN29LBz1u7o29D1Dw"
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

print("Consultando contagem de tabelas no Turso...", flush=True)
res = execute_pipeline([
    make_execute("SELECT COUNT(*) FROM questions"),
    make_execute("SELECT COUNT(*) FROM alternatives"),
    make_execute("SELECT COUNT(*) FROM explanations"),
    make_close()
])

results = res.get("results", [])
print("Questions:", results[0]["response"]["result"]["rows"][0][0]["value"])
print("Alternatives:", results[1]["response"]["result"]["rows"][0][0]["value"])
print("Explanations:", results[2]["response"]["result"]["rows"][0][0]["value"])
