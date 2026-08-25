import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br" in url:
        resp = entry.get("response", {})
        if resp.get("status") == 200:
            print("=" * 60)
            print("URL:", url)
            print("Request Headers:")
            for h in entry.get("request", {}).get("headers", []):
                print(f"  {h['name']}: {h['value']}")
            break
