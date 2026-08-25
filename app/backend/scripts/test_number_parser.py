import json
import re

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

all_questions = []
seen_ids = set()
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            for q in data.get("questions", []):
                qid = q.get("questionIdentifier") or q.get("_id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

def parse_q_number(q, fallback_idx):
    sku = q.get("sku", "")
    m = re.search(r"-\d{4}-(\d+)-", sku) or re.search(r"-(\d+)-R\d", sku) or re.search(r"-(\d+)", sku)
    if m:
        return int(m.group(1))
    return fallback_idx

parsed_numbers = [parse_q_number(q, idx) for idx, q in enumerate(all_questions, 1)]
print(f"Total questions: {len(parsed_numbers)}")
print(f"Min number: {min(parsed_numbers)}, Max number: {max(parsed_numbers)}")
print(f"Unique numbers: {len(set(parsed_numbers))}")
print(f"Missing numbers in 1..120: {set(range(1, 121)) - set(parsed_numbers)}")
