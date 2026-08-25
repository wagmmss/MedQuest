import json
import re
import sys
import os

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\USP_SP_2025.har"
print(f"Lendo HAR: {har_path} (Tamanho: {os.path.getsize(har_path)/(1024*1024):.2f} MB)")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")

all_questions = []
seen_ids = set()

for entry in entries:
    url = entry.get("request", {}).get("url", "")
    if "qbank-api.medcof.tech/v3/qbank/full" in url or "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            try:
                data = json.loads(text)
                for q in data.get("questions", []):
                    qid = q.get("questionIdentifier") or q.get("_id")
                    if qid and qid not in seen_ids:
                        seen_ids.add(qid)
                        all_questions.append(q)
            except Exception as e:
                print("Error parsing entry JSON:", e)

def parse_q_number(q, fallback_idx):
    sku = q.get("sku", "")
    m = re.search(r"-\d{4}-(\d+)-", sku) or re.search(r"-(\d+)-R\d", sku) or re.search(r"-(\d+)", sku)
    if m:
        return int(m.group(1))
    return fallback_idx

parsed_numbers = [parse_q_number(q, idx) for idx, q in enumerate(all_questions, 1)]
print(f"Total questões únicas: {len(all_questions)}")
print(f"Min: {min(parsed_numbers) if parsed_numbers else 'N/A'}, Max: {max(parsed_numbers) if parsed_numbers else 'N/A'}")
print(f"Únicos: {len(set(parsed_numbers))}")
if parsed_numbers:
    print(f"Faltantes em 1..{len(all_questions)}: {set(range(1, len(all_questions)+1)) - set(parsed_numbers)}")

# Check SKUs sample
print("Amostra SKUs:")
for q in all_questions[:5]:
    print(" ", q.get("sku"))
print("  ...")
for q in all_questions[-5:]:
    print(" ", q.get("sku"))
