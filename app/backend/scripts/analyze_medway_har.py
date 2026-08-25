import json
import base64
import re
from collections import defaultdict

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
print(f"Analisando MEDWAY.har: {har_path}")

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total de requisições no MEDWAY.har: {len(entries)}")

domains = defaultdict(int)
endpoints = []

for entry in entries:
    url = entry.get("request", {}).get("url", "")
    method = entry.get("request", {}).get("method", "")
    
    # Extract domain
    m = re.search(r"https?://([^/]+)", url)
    if m:
        domains[m.group(1)] += 1
        
    if "api" in url or "medway" in url or "graphql" in url or "question" in url or "simulado" in url:
        resp_status = entry.get("response", {}).get("status")
        resp_size = entry.get("response", {}).get("content", {}).get("size", 0)
        endpoints.append((method, url, resp_status, resp_size, entry))

print("\n--- Principais Domínios no HAR ---")
for d, cnt in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {d}: {cnt} requisições")

print(f"\n--- Endpoints de API/Dados Relevantes ({len(endpoints)}) ---")
for method, url, status, size, entry in endpoints[:20]:
    print(f"  [{method}] ({status}) {size}B -> {url[:100]}")

