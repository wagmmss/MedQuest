import json
import base64
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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
        print("=== EXPLANATION 218253 FULL FIELDS ===")
        for k in data.keys():
            print(f"Key: {k}")
            print(f"Val: {repr(data[k])[:120]}")
        break
