import json
import os

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Entries count:", len(har.get("log", {}).get("entries", [])))

modules_data = []
lessons_data = []
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
    elif "lesson-module" in url:
        modules_data.append((url, data))
    elif "/api/v2/lesson/" in url:
        lessons_data.append((url, data))
    elif "cms.medway.com.br" in url or "course" in url:
        all_cms_data.append((url, data))

print(f"focus_sp found: {focus_sp is not None}")
print(f"focus_rp found: {focus_rp is not None}")
print(f"modules_data found: {len(modules_data)}")
print(f"lessons_data found: {len(lessons_data)}")
print(f"all_cms_data found: {len(all_cms_data)}")

# Save focus data
if focus_sp:
    with open("go_focus_sp.json", "w", encoding="utf-8") as f:
        json.dump(focus_sp, f, ensure_ascii=False, indent=2)
if focus_rp:
    with open("go_focus_rp.json", "w", encoding="utf-8") as f:
        json.dump(focus_rp, f, ensure_ascii=False, indent=2)

with open("go_cms_data.json", "w", encoding="utf-8") as f:
    json.dump([{"url": u, "data": d} for u, d in all_cms_data], f, ensure_ascii=False, indent=2)

print("Saved extract files!")
