import json
import base64
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

questions = {}
explanations = {}

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    resp = entry.get("response", {})
    text = resp.get("content", {}).get("text", "")
    encoding = resp.get("content", {}).get("encoding", "")
    if text and encoding == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
    if not text:
        continue
    try:
        data = json.loads(text)
        if "api/v3/questions/" in url and "text-explanation" in url:
            qid = url.split("questions/")[1].split("/")[0]
            explanations[qid] = data
        elif "api/v3/questions/" in url and not "text-explanation" in url and not "reaction" in url and not "comments" in url and not "atualization" in url:
            qid = data.get("id") if isinstance(data, dict) else None
            if qid:
                questions[str(qid)] = data
    except Exception:
        pass

print(f"Total Questions: {len(questions)}")
print(f"Total Explanations: {len(explanations)}")

for qid in list(questions.keys())[:10]:
    q = questions[qid]
    exp = explanations.get(qid, {})
    
    # Check correct letter from options/question
    corr_q = q.get("correct_letters", [])
    
    # Check correct letter from explanation text
    corr_exp = []
    for let in ['a', 'b', 'c', 'd', 'e']:
        opt_text = (exp.get(f"option_{let}") or "").lower()
        short_text = (exp.get(f"short_option_{let}") or "").lower()
        full = opt_text + " " + short_text
        if "resposta correta" in full or "alternativa correta" in full or "gabarito" in full or "esta é a correta" in full or "é a correta" in full:
            corr_exp.append(let.upper())
            
    print(f"\nQID {qid}:")
    print(f"  Q corr_letters: {corr_q}")
    print(f"  Detected from exp: {corr_exp}")
    print(f"  Stem snippet: {q.get('content', '')[:60]}...")
    print(f"  Options: {[o.get('letter') for o in q.get('options', [])]}")
