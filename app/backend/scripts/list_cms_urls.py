import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Unique CMS URLs in HAR:")
cms_urls = {}
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "cms.medway.com.br" in url:
        status = entry.get("response", {}).get("status", 0)
        text = entry.get("response", {}).get("content", {}).get("text", "")
        cms_urls[url] = (status, len(text))

for u, (s, l) in sorted(cms_urls.items()):
    print(f" - [{s}] ({l}b) {u}")
