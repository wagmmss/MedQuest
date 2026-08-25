import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "api/v3/questions/408789/?track=5992995" in url:
        resp = entry.get("response", {})
        text = resp.get("content", {}).get("text", "")
        data = json.loads(text)
        print("Question 408789:")
        print("Content:", data.get("content")[:100])
        print("Options:")
        for opt in data.get("options", []):
            print(f"  [{opt.get('letter')}] ({opt.get('is_correct')}) {opt.get('content')[:60]}")
        print("Tags:", [t.get("name") for t in data.get("tag", [])])
        print("Year:", data.get("year"))
        break
