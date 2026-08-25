import json
import re

har_path = r"C:\Users\wmors\Downloads\USP_SP_2022.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

import base64
all_questions = []
seen_ids = set()

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        resp = entry.get("response", {})
        content = resp.get("content", {})
        text = content.get("text", "")
        encoding = content.get("encoding", "")
        if text:
            if encoding == "base64":
                text = base64.b64decode(text).decode("utf-8", errors="ignore")
            data = json.loads(text)
            for q in data.get("questions", []):
                qid = q.get("questionIdentifier") or q.get("_id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

print(f"Total questions: {len(all_questions)}")
print("\nSKUs de USP 2022:")
for idx, q in enumerate(all_questions):
    sku = q.get("sku", "")
    answers = q.get("answers", [])
    right_answers = [a for a in answers if a.get("rightAnswer")]
    print(f"[{idx+1}] SKU: {sku!r} | answers: {len(answers)} | right: {len(right_answers)} | anulada: {q.get('nulled')}")
