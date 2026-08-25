import json
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "qbank-api.medcof.tech/v3/qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            qs = data.get("questions", [])
            if qs:
                q = qs[0]
                print("KEYS IN QUESTION OBJECT:")
                for k, v in q.items():
                    if isinstance(v, str) and len(v) > 200:
                        print(f"  {k}: (str len {len(v)}) -> {v[:150]}...")
                    elif isinstance(v, (list, dict)):
                        print(f"  {k}: ({type(v).__name__}) -> {json.dumps(v, ensure_ascii=False)[:150]}...")
                    else:
                        print(f"  {k}: {v}")
                break
