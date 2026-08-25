import json

har_path = r"C:\Users\wmors\Downloads\MEDWAY.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

found = set()
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    for h in entry.get("request", {}).get("headers", []):
        if h.get("name", "").lower() == "authorization":
            found.add((url.split("?")[0], h.get("value")))

print("Found authorization headers in:")
for u, v in found:
    print(f"URL: {u}")
    print(f"Auth Token: {v[:40]}...")
