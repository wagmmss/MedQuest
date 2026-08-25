import json
import base64
from collections import defaultdict

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
print(f"Lendo HAR: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

questions = {}
explanations = {}
track_info = {}

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    resp = entry.get("response", {})
    content = resp.get("content", {})
    text = content.get("text", "")
    encoding = content.get("encoding", "")
    
    if text and encoding == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
        
    if not text:
        continue
        
    try:
        data = json.loads(text)
    except Exception:
        continue
        
    if "api/v3/track/" in url and "questions" in url:
        qs = data if isinstance(data, list) else (data.get("results") or data.get("questions") or [])
        for q in qs:
            qid = q.get("id")
            if qid:
                questions[qid] = q
    elif "api/v3/questions/" in url and "text-explanation" in url:
        qid = url.split("questions/")[1].split("/")[0]
        explanations[int(qid) if qid.isdigit() else qid] = data
    elif "api/v3/questions/" in url and not "text-explanation" in url and not "reaction" in url:
        qid = data.get("id") if isinstance(data, dict) else None
        if qid:
            questions[qid] = data
    elif "api/v3/track/" in url and "fast" in url:
        track_info = data

print(f"Total de questões identificadas: {len(questions)}")
print(f"Total de resoluções completas (text-explanation) identificadas: {len(explanations)}")
print(f"Track Info: {track_info}")

if questions:
    sample_qid = list(questions.keys())[0]
    sample_q = questions[sample_qid]
    print("\n--- Exemplo de Questão ---")
    print(f"ID: {sample_qid}")
    print(f"Institution: {sample_q.get('institution')}")
    print(f"Year: {sample_q.get('year')}")
    print(f"Speciality: {sample_q.get('speciality')}")
    print(f"Content: {sample_q.get('content', '')[:150]}...")
    print(f"Options count: {len(sample_q.get('options', []))}")
    print(f"Options: {sample_q.get('options')}")

if explanations:
    sample_eid = list(explanations.keys())[0]
    sample_e = explanations[sample_eid]
    print("\n--- Exemplo de Resolução / Explicação ---")
    print(f"Question ID: {sample_eid}")
    print("Keys:", list(sample_e.keys()))
    print(f"Introduction: {sample_e.get('introduction', '')[:150]}...")
    print(f"Conclusion: {sample_e.get('conclusion', '')[:150]}...")
    print(f"Option A: {sample_e.get('option_a', '')[:100]}...")
