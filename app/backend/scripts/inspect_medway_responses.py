import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br/api" in url:
        resp = entry.get("response", {})
        content = resp.get("content", {})
        text = content.get("text", "")
        encoding = content.get("encoding", "")
        if text:
            if encoding == "base64":
                text = base64.b64decode(text).decode("utf-8", errors="ignore")
            try:
                data = json.loads(text)
                print("=" * 60)
                print(f"URL: {url}")
                if isinstance(data, dict):
                    print("Keys:", list(data.keys()))
                    if "results" in data:
                        print("Results count:", len(data["results"]))
                        if data["results"]:
                            print("Sample result keys:", list(data["results"][0].keys()))
                            print("Sample item:", json.dumps(data["results"][0], indent=2)[:300])
                    elif "questions" in data or "items" in data:
                        print("Questions/Items in dict")
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
                    if data:
                        print("Sample item keys:", list(data[0].keys()) if isinstance(data[0], dict) else type(data[0]))
                        print("Sample item:", json.dumps(data[0], indent=2)[:300])
            except Exception as e:
                pass
