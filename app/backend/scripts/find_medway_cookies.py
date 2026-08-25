import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br" in url:
        cookies = entry.get("request", {}).get("cookies", [])
        if cookies:
            print("Cookies found in", url)
            for c in cookies:
                print(f"  {c.get('name')}: {c.get('value')[:30]}...")
            break
