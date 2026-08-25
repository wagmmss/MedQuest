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
    url = entry.get("request", {}).get("url", "")
    if "qbank-api.medcof.tech/v3/qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            qs = data.get("questions", [])
            for q in qs:
                qid = q.get("questionIdentifier") or q.get("_id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

print(f"Total de questoes unicas no HAR: {len(all_questions)}")

# Check question numbering / skus
skus = [q.get("sku") for q in all_questions]
print(f"SKUs encontrados ({len(skus)}):")
for s in skus[:10]:
    print(" ", s)
print("  ...")
for s in skus[-5:]:
    print(" ", s)

# Check answers structure
print("\n--- Estrutura detalhada de answers da Questao 1 ---")
q0 = all_questions[0]
for idx, a in enumerate(q0.get("answers", [])):
    print(f"  Alt {idx} ({chr(65+idx)}):")
    for k, v in a.items():
        print(f"    {k}: {v}")

# Check tags structure
print("\n--- Tags da Questao 1 ---")
for t in q0.get("tags", []):
    print(f"  Tag: {t.get('name')} (id={t.get('identifier')})")

