import json
import base64
import sys
import io
import re
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

questions = {}
explanations = {}
track_order = []

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
        if "api/v3/track/" in url and "questions" in url:
            qs = data if isinstance(data, list) else (data.get("results") or data.get("questions") or [])
            for q in qs:
                qid = str(q.get("id"))
                if qid and qid not in track_order:
                    track_order.append(qid)
        elif "api/v3/questions/" in url and "text-explanation" in url:
            qid = url.split("questions/")[1].split("/")[0]
            explanations[qid] = data
        elif "api/v3/questions/" in url and not "text-explanation" in url and not "reaction" in url and not "comments" in url and not "atualization" in url:
            qid = data.get("id") if isinstance(data, dict) else None
            if qid:
                questions[str(qid)] = data
    except Exception:
        pass

def extract_correct_letter(exp_dict, options_list):
    if not exp_dict:
        return "A"
    
    # 1. Check strong markers
    for opt in options_list:
        let = opt.get("letter", "").lower()
        opt_text = exp_dict.get(f"option_{let}", "") or ""
        short_text = exp_dict.get(f"short_option_{let}", "") or ""
        combined = (opt_text + " " + short_text).lower()
        
        # Check if explicitly correct
        if re.search(r"<strong>\s*corret[ao]!?\s*</strong>", combined) or \
           re.search(r"\bcorreta!?\b", combined[:50]) or \
           "resposta correta" in combined or \
           "esta é a resposta correta" in combined or \
           "alternativa correta" in combined or \
           "esta é a correta" in combined or \
           "gabarito" in combined:
            return let.upper()
            
    # 2. Check if other options are marked "Incorreta"
    candidates = []
    for opt in options_list:
        let = opt.get("letter", "").lower()
        opt_text = exp_dict.get(f"option_{let}", "") or ""
        short_text = exp_dict.get(f"short_option_{let}", "") or ""
        combined = (opt_text + " " + short_text).lower()
        if not re.search(r"<strong>\s*incorret[ao]!?\s*</strong>", combined) and not combined.startswith("<p><strong>incorreta") and not "incorreta." in combined[:50]:
            candidates.append(let.upper())
            
    if len(candidates) == 1:
        return candidates[0]
        
    return candidates[0] if candidates else "A"

gabaritos = []
for qid in track_order:
    q = questions.get(qid, {})
    exp = explanations.get(qid, {})
    opts = q.get("options", [])
    g = extract_correct_letter(exp, opts)
    gabaritos.append((qid, g))

print(f"Total de questões avaliadas: {len(gabaritos)}")
print(f"Distribuição de Gabaritos:")
counts = defaultdict(int)
for qid, g in gabaritos:
    counts[g] += 1
for k, v in sorted(counts.items()):
    print(f"  Letra {k}: {v} questões ({v/len(gabaritos)*100:.1f}%)")

print("\nPrimeiros 10 gabaritos:")
for idx, (qid, g) in enumerate(gabaritos[:10], start=1):
    print(f"  Q{idx:02d} (ID: {qid}): Letra {g}")
