import json
import base64
from collections import defaultdict

har_path = r"C:\Users\wmors\Downloads\UNIFESP_2020-2026.har"
print(f"Lendo HAR: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")

all_questions = []
seen_ids = set()

test_infos = []

for entry in entries:
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        resp = entry.get("response", {})
        content = resp.get("content", {})
        text = content.get("text", "")
        encoding = content.get("encoding", "")
        if text:
            if encoding == "base64":
                text = base64.b64decode(text).decode("utf-8", errors="ignore")
            try:
                data = json.loads(text)
                t_name = data.get("name")
                t_info = data.get("prebuiltTestInfo")
                t_count = data.get("questionsCount")
                qs = data.get("questions", [])
                test_infos.append((url, t_name, t_count, len(qs)))
                for q in qs:
                    qid = q.get("questionIdentifier") or q.get("_id")
                    if qid and qid not in seen_ids:
                        seen_ids.add(qid)
                        all_questions.append(q)
            except Exception as e:
                print("Error parsing JSON:", e)

print(f"Total questoes unicas extraidas: {len(all_questions)}")

# Group by year found on each question
by_year = defaultdict(list)
for q in all_questions:
    yr = q.get("year")
    sku = q.get("sku", "")
    by_year[yr].append(q)

print("\n--- Distribuicao por Ano no HAR ---")
for yr, qs in sorted(by_year.items(), key=lambda x: str(x[0]), reverse=True):
    print(f"  Ano {yr}: {len(qs)} questoes (Amostra SKU: {qs[0].get('sku')!r})")

