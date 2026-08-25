import json
import base64
from collections import defaultdict

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
print(f"Lendo HAR: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

questions = {}
explanations = {}
track_questions_order = []

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
            if qid and qid not in track_questions_order:
                track_questions_order.append(qid)
    elif "api/v3/questions/" in url and "text-explanation" in url:
        qid = url.split("questions/")[1].split("/")[0]
        explanations[int(qid) if qid.isdigit() else qid] = data
    elif "api/v3/questions/" in url and not "text-explanation" in url and not "reaction" in url and not "comments" in url and not "atualization" in url:
        qid = data.get("id") if isinstance(data, dict) else None
        if qid:
            questions[qid] = data

print(f"Total de questões na ordem do track: {len(track_questions_order)}")
print(f"Total de questões completas (com content e options): {len(questions)}")
print(f"Total de resoluções completas (text-explanation): {len(explanations)}")

if questions:
    sample_qid = list(questions.keys())[0]
    sample_q = questions[sample_qid]
    print("\n--- Exemplo de Questão Completa ---")
    print(f"ID: {sample_qid}")
    print(f"Content: {sample_q.get('content', '')[:120]}...")
    print(f"Year: {sample_q.get('year')}")
    print(f"Tags: {[t.get('name') for t in sample_q.get('tag', [])]}")
    print("Options:")
    for opt in sample_q.get("options", []):
        print(f"  [{opt.get('letter')}] {opt.get('content')[:50]}")

if explanations:
    sample_eid = list(explanations.keys())[0]
    sample_e = explanations[sample_eid]
    print("\n--- Exemplo de Explicação ---")
    print(f"Question ID: {sample_eid}")
    print(f"Intro: {sample_e.get('introduction', '')[:100]}...")
    print(f"Conclusion: {sample_e.get('conclusion', '')[:100]}...")
    print(f"Option A: {sample_e.get('option_a', '')[:60]}...")
