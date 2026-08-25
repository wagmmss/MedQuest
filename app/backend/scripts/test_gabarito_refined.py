import json
import base64
import html
import re
from collections import defaultdict

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

def extract_gabarito(exp_dict, options_list):
    if not exp_dict:
        return "A"
        
    scores = {}
    for opt in options_list:
        let = opt.get("letter", "").lower()
        raw_opt = exp_dict.get(f"option_{let}", "") or ""
        raw_short = exp_dict.get(f"short_option_{let}", "") or ""
        
        # Clean html
        txt = html.unescape(raw_opt + " " + raw_short)
        txt_clean = re.sub(r"<[^>]+>", " ", txt).strip().lower()
        
        is_correct = False
        is_incorrect = False
        
        if "incorret" in txt_clean[:40] or "errad" in txt_clean[:40] or "distrator" in txt_clean[:40]:
            is_incorrect = True
        if "corret" in txt_clean[:40] or "certa" in txt_clean[:40] or "gabarito" in txt_clean[:40] or "resposta certa" in txt_clean or "resposta correta" in txt_clean or "esta é a resposta correta" in txt_clean:
            is_correct = True
            
        if is_correct and not is_incorrect:
            scores[let.upper()] = 10
        elif is_incorrect:
            scores[let.upper()] = -10
        else:
            scores[let.upper()] = 0
            
    # Find max score
    if scores:
        best_let = max(scores.items(), key=lambda x: x[1])[0]
        return best_let
    return "A"

gabaritos = []
for qid in track_order:
    q = questions.get(qid, {})
    exp = explanations.get(qid, {})
    opts = q.get("options", [])
    g = extract_gabarito(exp, opts)
    gabaritos.append((qid, g))

counts = defaultdict(int)
for qid, g in gabaritos:
    counts[g] += 1

print("Distribuição de Gabaritos Refinada:")
for k, v in sorted(counts.items()):
    print(f"  Letra {k}: {v} questões ({v/len(gabaritos)*100:.1f}%)")

print("\nPrimeiros 15 gabaritos:")
for idx, (qid, g) in enumerate(gabaritos[:15], start=1):
    print(f"  Q{idx:02d} (ID: {qid}): Letra {g}")
