import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    resp = entry.get("response", {})
    content = resp.get("content", {})
    text = content.get("text", "")
    encoding = content.get("encoding", "")
    if text and encoding == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
    if not text:
        continue
    try:
        data = json.loads(text)
        if "content" in data and "options" in data:
            print("Encontrada questão com content e options em URL:", url)
            print("ID:", data.get("id"))
            print("Content:", data.get("content")[:100])
            print("Options:")
            for opt in data.get("options", []):
                print("  Opt:", opt.get("letter"), opt.get("content")[:60])
            break
    except Exception:
        pass
