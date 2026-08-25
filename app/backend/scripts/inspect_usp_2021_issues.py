import json
import base64

har_path = r"C:\Users\wmors\Downloads\USP_SP_2021.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

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

for idx, q in enumerate(all_questions):
    sku = q.get("sku", "")
    answers = q.get("answers", [])
    right_answers = [a for a in answers if a.get("rightAnswer")]
    if len(answers) < 4 or len(right_answers) != 1:
        print(f"[{idx+1}] Issue SKU: {sku!r} | answers: {len(answers)} | right: {len(right_answers)} | nulled: {q.get('nulled')} | nulledReason: {q.get('nulledReason')}")
        for aidx, a in enumerate(answers):
            print(f"   Alt {aidx}: right={a.get('rightAnswer')} | {a.get('answer')}")

print("\nSKUs list:")
for idx, q in enumerate(all_questions):
    print(f"  [{idx+1}] {q.get('sku')}")
