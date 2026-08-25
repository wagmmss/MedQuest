import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "text-explanation" in url:
        resp = entry.get("response", {})
        print("Status:", resp.get("status"))
        req_headers = entry.get("request", {}).get("headers", [])
        print("Request Headers:")
        for h in req_headers:
            print(f"  {h.get('name')}: {h.get('value')}")
        resp_headers = entry.get("response", {}).get("headers", [])
        print("Response Headers:")
        for h in resp_headers:
            print(f"  {h.get('name')}: {h.get('value')}")
        break
