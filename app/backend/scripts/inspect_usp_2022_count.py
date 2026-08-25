import json
import base64

har_path = r"C:\Users\wmors\Downloads\USP_SP_2022.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")

for i, entry in enumerate(entries):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        resp = entry.get("response", {})
        content = resp.get("content", {})
        text = content.get("text", "")
        encoding = content.get("encoding", "")
        
        if text:
            try:
                if encoding == "base64":
                    text = base64.b64decode(text).decode("utf-8", errors="ignore")
                data = json.loads(text)
                print(f"\nEntry [{i}] URL: {url}")
                print(f"  questionsCount: {data.get('questionsCount')}, questionsLimit: {data.get('questionsLimit')}")
                print(f"  questions in this page: {len(data.get('questions', []))}")
                print(f"  pagination: {data.get('pagination')}")
                print(f"  testInfo: {data.get('prebuiltTestInfo')}")
            except Exception as e:
                print(f"Error on entry {i}:", e)
