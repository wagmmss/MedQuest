import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Inspecionando chamadas bem sucedidas (200 OK) a cms.medway.com.br no HAR:")
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br/api/v3" in url:
        resp = entry.get("response", {})
        if resp.get("status") == 200:
            print(f"\nURL: {url}")
            print("Request Headers:")
            for h in entry.get("request", {}).get("headers", []):
                print(f"  {h['name']}: {h['value']}")
            print("Request Cookies in entry:")
            for c in entry.get("request", {}).get("cookies", []):
                print(f"  {c}")
            break
