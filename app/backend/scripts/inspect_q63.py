import json
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            for q in data.get("questions", []):
                sku = q.get("sku", "")
                if "63" in sku:
                    print("SKU:", sku)
                    print("Statement:", q.get("statement")[:200])
                    print("Nulled:", q.get("nulled"))
                    print("NulledReason:", q.get("nulledReason"))
                    for idx, a in enumerate(q.get("answers", [])):
                        print(f"Alt {chr(65+idx)}: is_right={a.get('rightAnswer')} | {a.get('answer')}")
                    print("Comment:", q.get("comment")[:300])

