import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br/api/v3/questions/" in url and "text-explanation" in url:
        headers = entry.get("request", {}).get("headers", [])
        print("URL de Explicação:", url)
        for h in headers:
            if h.get("name", "").lower() in ["authorization", "cookie", "x-csrftoken"]:
                print(f"  Header: {h.get('name')}: {h.get('value')[:60]}...")
        break
