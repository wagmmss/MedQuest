import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "api/v3/questions/218253/text-explanation" in url:
        resp = entry.get("response", {})
        text = resp.get("content", {}).get("text", "")
        encoding = resp.get("content", {}).get("encoding", "")
        if encoding == "base64":
            text = base64.b64decode(text).decode("utf-8", errors="ignore")
        data = json.loads(text)
        print("=== TEXT EXPLANATION 218253 ===")
        for k, v in data.items():
            print(f"[{k}]: {str(v)[:200]}")
        break
