import json

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)

print(f"SP Keys: {list(sp.keys()) if isinstance(sp, dict) else len(sp)}")
if isinstance(sp, dict):
    for k, v in sp.items():
        if isinstance(v, list):
            print(f"  SP {k}: {len(v)} items")
            if len(v) > 0 and isinstance(v[0], dict):
                print(f"    Sample item keys: {list(v[0].keys())}")
                print(f"    Sample item: {v[0]}")

with open("go_cms_data.json", "r", encoding="utf-8") as f:
    cms = json.load(f)

print(f"\nTotal CMS items: {len(cms)}")
modules = {}
for item in cms:
    url = item["url"]
    data = item["data"]
    if "lesson-module" in url and isinstance(data, dict):
        mod_id = data.get("id") or url.split("/")[-2]
        name = data.get("name") or data.get("title")
        if name:
            modules[mod_id] = data

print(f"Unique modules extracted: {len(modules)}")
for mid, m in list(modules.items())[:10]:
    print(f"  Module {mid}: {m.get('name')} | lessons: {len(m.get('lessons', []))}")
