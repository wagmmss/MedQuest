import json
import base64
import re

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

def parse_sku_qnum(sku: str, inst_code: str, year: int, fallback_idx: int) -> tuple[int | None, bool]:
    sku = (sku or "").strip()
    if "DISCURSIVA" in sku or "TEEM" in sku:
        return None, False
        
    norm_inst = inst_code.upper().replace("-", "")
    norm_sku = sku.upper().replace("-", "").replace(" ", "")
    
    m = re.search(r"R\dQ(\d+)", sku, re.IGNORECASE)
    if m:
        return int(m.group(1)), True
        
    m = re.search(r"-Q?(\d+)-R\d", sku, re.IGNORECASE)
    if m and norm_inst in norm_sku:
        return int(m.group(1)), True
        
    m = re.search(rf"{year}-(\d+)", sku)
    if m and norm_inst in norm_sku:
        return int(m.group(1)), True
        
    return fallback_idx, True

nums = []
for idx, q in enumerate(all_questions, 1):
    num, keep = parse_sku_qnum(q.get("sku", ""), "USP-SP", 2021, idx)
    if keep:
        nums.append(num)

print(f"Total parsed: {len(nums)}")
print(f"Min: {min(nums)}, Max: {max(nums)}, Unicos: {len(set(nums))}")
print(f"Missing in 1..120: {set(range(1, 121)) - set(nums)}")
