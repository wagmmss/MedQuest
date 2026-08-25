import json
import base64
import re

har_path = r"C:\Users\wmors\Downloads\USP_SP_2022.har"
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

def parse_sku_qnum(sku: str, fallback: int) -> tuple[int, bool]:
    sku = (sku or "").strip()
    if "DISCURSIVA" in sku or "TEEM" in sku:
        return None, False
        
    m = re.search(r"R\dQ(\d+)", sku, re.IGNORECASE)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-Q?(\d+)-R\d", sku, re.IGNORECASE)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-\d{4}-(\d+)", sku)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-(\d+)", sku)
    if m:
        return int(m.group(1)), True
        
    return fallback, True

filtered = []
for idx, q in enumerate(all_questions, 1):
    num, keep = parse_sku_qnum(q.get("sku", ""), idx)
    if keep:
        filtered.append((num, q))

print(f"Total apos filtro: {len(filtered)}")
nums = [num for num, q in filtered]
print(f"Min: {min(nums)}, Max: {max(nums)}, Unicos: {len(set(nums))}")
print(f"Missing in 1..100: {set(range(1, 101)) - set(nums)}")
