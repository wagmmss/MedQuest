import json
import base64

har_path = r"C:\Users\wmors\Downloads\HSL_2020-2026.har"
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
                print(f"URL: {url}")
                print(f"  Name: {data.get('name')}")
                print(f"  questionsCount: {data.get('questionsCount')}")
                print(f"  pagination: {data.get('pagination')}")
            except Exception as e:
                pass
