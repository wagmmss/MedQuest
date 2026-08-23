import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "digital-mentoring" in url or "lesson-schedule" in url:
        status = entry.get("response", {}).get("status", 0)
        content = entry.get("response", {}).get("content", {})
        text = content.get("text", "")
        print(f"[{status}] ({len(text)}b) {url}")
        if text:
            print(f"  Preview: {text[:200]}")
