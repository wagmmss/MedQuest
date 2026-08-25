import json
import base64
import html
import re

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "api/v3/questions/218257/text-explanation" in url:
        resp = entry.get("response", {})
        text = resp.get("content", {}).get("text", "")
        encoding = resp.get("content", {}).get("encoding", "")
        if encoding == "base64":
            text = base64.b64decode(text).decode("utf-8", errors="ignore")
        data = json.loads(text)
        print("Q218257:")
        for let in ['a', 'b', 'c', 'd']:
            raw = data.get(f"option_{let}", "")
            clean = html.unescape(raw)
            print(f"[{let.upper()}]:", clean[:100])
        break
