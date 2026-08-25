import json
import base64
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Procurando gabaritos no HAR:")
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    resp = entry.get("response", {})
    text = resp.get("content", {}).get("text", "")
    encoding = resp.get("content", {}).get("encoding", "")
    if text and encoding == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
    if not text:
        continue
    try:
        data = json.loads(text)
        if "correct" in text.lower() or "right" in text.lower() or "gabarito" in text.lower():
            print(f"Match em URL: {url[:100]}")
    except Exception:
        pass
