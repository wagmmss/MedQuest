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

for i, entry in enumerate(entries):
    url = entry.get("request", {}).get("url", "")
    if "qbank-api.medcof.tech/v3/qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            qs = data.get("questions", [])
            print(f"\nEntry {i} -> URL: {url}")
            print(f"data['questions'] length: {len(qs)}")
            if len(qs) > 0:
                print(f"Type of first element: {type(qs[0])}")
                print(f"Content of first element: {json.dumps(qs[0], ensure_ascii=False)[:500]}")
            break
