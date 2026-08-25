import json
import base64

har_path = r"C:\Users\wmors\Downloads\UNICAMP_2026.har"
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
            data = json.loads(text)
            print("URL:", url)
            print("  questionsCount:", data.get("questionsCount"))
            print("  totalElements:", data.get("pagination", {}).get("totalElements"))
            print("  totalPages:", data.get("pagination", {}).get("totalPages"))
            print("  page:", data.get("pagination", {}).get("page"))
