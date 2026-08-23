import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

modules = {}
with open("go_modules_raw.json", "r", encoding="utf-8") as f:
    raw_mods = json.load(f)
    for m in raw_mods:
        modules[str(m["id"])] = {"name": m["name"], "lessons": [], "durations": []}

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    text = entry.get("response", {}).get("content", {}).get("text", "")
    if not text:
        continue
    
    # Check if this URL contains lesson-schedule or lesson details
    try:
        data = json.loads(text)
    except Exception:
        continue
        
    # Check digital mentoring or lesson module schedules
    if isinstance(data, dict):
        # Could be schedule with items
        items = data.get("items") or data.get("lessons") or []
        mod = data.get("module") or data.get("lesson_module")
        mod_id = str(mod.get("id")) if isinstance(mod, dict) else None
        if not mod_id:
            for mid in modules.keys():
                if f"/{mid}/" in url:
                    mod_id = mid
                    break
        if mod_id and mod_id in modules:
            if isinstance(items, list):
                for it in items:
                    name = it.get("name") or it.get("title")
                    dur = it.get("video_duration") or it.get("duration") or 0
                    modules[mod_id]["lessons"].append({"name": name, "duration": dur, "url": url})

    elif isinstance(data, list):
        for elem in data:
            if isinstance(elem, dict):
                mod = elem.get("module") or elem.get("lesson_module")
                mod_id = str(mod.get("id")) if isinstance(mod, dict) else None
                if mod_id and mod_id in modules:
                    name = elem.get("name") or elem.get("title")
                    dur = elem.get("video_duration") or elem.get("duration") or 0
                    modules[mod_id]["lessons"].append({"name": name, "duration": dur, "url": url})

print("Summary of modules with lessons in HAR:")
for mid, m in modules.items():
    print(f"Module {mid}: {m['name']} -> {len(m['lessons'])} lessons")
    for l in m['lessons'][:5]:
        print(f"    - {l['name']}: {l['duration']}s")
