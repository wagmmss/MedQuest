import json
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])

all_questions = []
seen_ids = set()

for entry in entries:
    url = entry.get("request", {}) .get("url", "")
    if "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            qs = data.get("questions", [])
            for q in qs:
                qid = q.get("_id") or q.get("id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

print(f"Total questoes unicas extraidas do HAR: {len(all_questions)}")

if all_questions:
    sample = all_questions[0]
    print("\n--- Chaves da primeira questao ---")
    for k, v in sample.items():
        vstr = str(v)
        if len(vstr) > 100:
            vstr = vstr[:100] + "... (truncated)"
        print(f"  {k}: {type(v).__name__} = {vstr}")
        
    print("\n--- Detalhes das alternativas da primeira questao ---")
    alts = sample.get("alternatives", [])
    for idx, alt in enumerate(alts):
        print(f"  Alt {idx}: {alt}")
        
    print("\n--- Comentario / Explicacao da primeira questao ---")
    for k in ["comment", "explanation", "resolution", "teacherComment", "comments"]:
        if k in sample:
            print(f"  {k}: {sample[k]}")

