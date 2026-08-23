import json
import os
import glob

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"

print(f"Reading {har_path}...")
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")

endpoints = set()
responses = []

for i, entry in enumerate(entries):
    req = entry.get("request", {})
    url = req.get("url", "")
    endpoints.add(url.split("?")[0])
    
    resp = entry.get("response", {})
    content = resp.get("content", {})
    text = content.get("text", "")
    mime = content.get("mimeType", "")
    
    if "json" in mime and text:
        try:
            data = json.loads(text)
            responses.append((url, data))
        except Exception:
            pass

print(f"Parsed {len(responses)} JSON responses across {len(endpoints)} endpoints.")
print("\nKey endpoints:")
for ep in sorted(endpoints):
    if "medway" in ep or "katomart" in ep or "course" in ep or "lesson" in ep or "module" in ep or "theme" in ep or "foco" in ep:
        print(" -", ep)

with open("go_endpoints.txt", "w", encoding="utf-8") as f:
    for ep in sorted(endpoints):
        f.write(ep + "\n")
