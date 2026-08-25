import json

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")
for idx, entry in enumerate(entries):
    url = entry.get("request", {}).get("url", "")
    method = entry.get("request", {}).get("method", "")
    status = entry.get("response", {}).get("status")
    print(f"{idx+1}. [{method}] ({status}) {url}")
