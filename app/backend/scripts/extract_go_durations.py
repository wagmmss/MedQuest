import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

print("Searching for lesson / course durations in HAR...")
duration_items = []
courses_found = []

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
    
    # Search recursively for duration or lessons
    def find_lessons(obj, path=""):
        if isinstance(obj, dict):
            if "duration" in obj or "video_duration" in obj or "lessons" in obj or "modules" in obj:
                duration_items.append((url, obj))
            for k, v in obj.items():
                find_lessons(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, elem in enumerate(obj):
                find_lessons(elem, f"{path}[{i}]")
                
    find_lessons(data)

print(f"Found {len(duration_items)} duration / lesson candidate objects in HAR.")

# Let's inspect some of them
lessons = []
for url, item in duration_items:
    if isinstance(item, dict) and ("duration" in item or "video_duration" in item):
        title = item.get("title") or item.get("name")
        dur = item.get("duration") or item.get("video_duration")
        if title and dur:
            lessons.append((title, dur, url))

print(f"Extracted {len(lessons)} lessons with duration from HAR:")
for t, d, u in lessons[:20]:
    print(f"  - {t}: {d} (URL: {u})")
