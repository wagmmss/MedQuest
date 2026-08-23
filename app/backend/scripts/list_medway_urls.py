import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

app_urls = set()
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "medway.com.br" in url:
        app_urls.add(url)

print(f"Total Medway URLs: {len(app_urls)}")
for u in sorted(app_urls):
    print(" -", u)
