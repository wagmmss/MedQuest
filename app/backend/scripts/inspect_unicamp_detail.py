import json
import base64

har_path = r"C:\Users\wmors\Downloads\UNICAMP_2020-2025.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

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
                t_name = data.get("name")
                qs = data.get("questions", [])
                if qs:
                    q = qs[0]
                    print(f"\n--- {t_name} (Q1) ---")
                    print("SKU:", q.get("sku"))
                    print("Year:", q.get("year"))
                    print("Statement:", q.get("statement")[:120])
                    print("TakeHomeMessage:", q.get("takeHomeMessage")[:120] if q.get("takeHomeMessage") else "None")
                    print("Comment:", q.get("comment")[:120] if q.get("comment") else "None")
                    print("Answers count:", len(q.get("answers", [])))
            except Exception as e:
                pass
