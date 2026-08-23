import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

modules_json = None
for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "lesson-subject/20366/modules/" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            modules_json = json.loads(text)
            break

if modules_json:
    print(f"Extracted modules JSON! Count: {len(modules_json)}")
    with open("go_modules_raw.json", "w", encoding="utf-8") as f:
        json.dump(modules_json, f, ensure_ascii=False, indent=2)
        
    for i, m in enumerate(modules_json):
        print(f"\n[{i+1}] Module ID: {m.get('id')} | Name: {m.get('name')}")
        lessons = m.get("lessons", [])
        print(f"    Lessons count: {len(lessons)}")
        total_sec = 0
        for l in lessons:
            dur = l.get("video_duration") or l.get("duration") or 0
            total_sec += dur
            print(f"      - Lesson {l.get('id')}: {l.get('name')} | {dur}s ({dur/3600:.2f}h)")
        print(f"    Total module duration: {total_sec/3600:.2f}h")
else:
    print("Could not find lesson-subject/20366/modules/ with content.")
