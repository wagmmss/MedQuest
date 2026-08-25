import json
import base64
from collections import defaultdict

har_path = r"C:\Users\wmors\Downloads\SCMSP_2020-2026.har"
print(f"Lendo HAR: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

test_map = defaultdict(list)

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
            try:
                data = json.loads(text)
                t_name = data.get("name") or "Sem nome"
                t_id = url.split("?")[0].split("/")[-1]
                qs = data.get("questions", [])
                for q in qs:
                    test_map[(t_id, t_name)].append(q)
            except Exception as e:
                pass

print(f"Total de testes encontrados no HAR: {len(test_map)}")
for (tid, tname), qs in sorted(test_map.items(), key=lambda x: x[0][1]):
    seen = set()
    uniq_qs = []
    for q in qs:
        qid = q.get("questionIdentifier") or q.get("_id")
        if qid not in seen:
            seen.add(qid)
            uniq_qs.append(q)
            
    years_in_test = set(q.get("year") for q in uniq_qs)
    print(f"\n[TEST] {tname} (ID: {tid}) -> {len(uniq_qs)} questoes unicas | Anos nas questoes: {years_in_test}")
    if uniq_qs:
        for q in uniq_qs[:3]:
            print(f"   - SKU: {q.get('sku')!r} | Ano={q.get('year')} | Alts: {len(q.get('answers', []))} | Gabarito: {[chr(65+i) for i, a in enumerate(q.get('answers', [])) if a.get('rightAnswer')]}")
