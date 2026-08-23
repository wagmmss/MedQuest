import json
import os

har_path = r"C:\Users\wmors\Desktop\Medicina Preventiva.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Entries count:", len(har.get("log", {}).get("entries", [])))

modules_data = []
focus_sp = None
focus_rp = None
all_cms_data = []

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    content = entry.get("response", {}).get("content", {})
    text = content.get("text", "")
    if not text:
        continue
    try:
        data = json.loads(text)
    except Exception:
        continue
        
    if "student-domain/focus/?institution=26" in url:
        focus_sp = data
    elif "student-domain/focus/?institution=27" in url:
        focus_rp = data
    elif "/modules/" in url:
        modules_data.append((url, data))
    elif "cms.medway.com.br" in url:
        all_cms_data.append((url, data))

print(f"focus_sp found: {focus_sp is not None}")
print(f"focus_rp found: {focus_rp is not None}")
print(f"modules_data found: {len(modules_data)}")
print(f"all_cms_data found: {len(all_cms_data)}")

if focus_sp:
    with open("preventiva_focus_sp.json", "w", encoding="utf-8") as f:
        json.dump(focus_sp, f, ensure_ascii=False, indent=2)
if focus_rp:
    with open("preventiva_focus_rp.json", "w", encoding="utf-8") as f:
        json.dump(focus_rp, f, ensure_ascii=False, indent=2)

if modules_data:
    for u, d in modules_data:
        print(f"Modules URL: {u}")
        if isinstance(d, list):
            print(f"Found {len(d)} modules in response!")
            with open("preventiva_modules_raw.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            break

print("Extracted Preventiva HAR successfully!")
