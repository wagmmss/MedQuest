import json
import base64

har_path = r"C:\Users\wmors\Downloads\UNICAMP_2026.har"
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

print(f"Total questions unicas: {len(all_questions)}")
for idx, q in enumerate(all_questions, 1):
    print(f"[{idx}] SKU: {q.get('sku')!r} | answers: {len(q.get('answers', []))} | nulled: {q.get('nulled')}")
