import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
print(f"Lendo HAR anterior: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

questions = {}
explanations = {}

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

print(f"Total de questões identificadas no MEDWAY.har: {len(questions)}")
print(f"Total de resoluções (text-explanation) identificadas: {len(explanations)}")

if explanations:
    for qid, exp in list(explanations.items())[:3]:
        print(f"\n[RESOLUÇÃO QID {qid}]")
        print("  Intro:", exp.get("introduction", "")[:100])
        print("  Conclusion:", exp.get("conclusion", "")[:100])
        print("  Option A:", exp.get("option_a", "")[:100])
