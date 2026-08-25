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
print(f"Total entries: {len(entries)}")

qbank_entries = []
for i, entry in enumerate(entries):
    req = entry.get("request", {})
    url = req.get("url", "")
    resp = entry.get("response", {})
    content = resp.get("content", {})
    text = content.get("text", "")
    
    if "medcof.tech" in url and text:
        try:
            data = json.loads(text)
            qbank_entries.append((i, url, data))
        except Exception:
            pass

print(f"Found {len(qbank_entries)} MedCof API JSON responses:")
for idx, url, data in qbank_entries:
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f"\n--- Entry [{idx}] URL: {url} ---")
        print(f"Keys: {keys}")
        
        # Check for questions / list
        for k in ["questions", "items", "data", "results", "testInfo", "prebuiltTestInfo"]:
            if k in data:
                val = data[k]
                vlen = len(val) if isinstance(val, (list, dict)) else 'N/A'
                print(f"  Field '{k}': type={type(val).__name__}, len={vlen}")

