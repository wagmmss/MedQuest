import json

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)

print(f"SP is list of {len(sp)} items")
for i, item in enumerate(sp[:10]):
    print(f"\nItem {i+1}:")
    for k, v in item.items():
        if k in ["name", "title", "discipline", "specialty", "module", "focus", "area", "theme", "course", "weight", "frequency", "priority"]:
            print(f"  {k}: {v}")
        elif isinstance(v, (str, int, float, bool)):
            print(f"  {k}: {v}")
        elif isinstance(v, dict):
            print(f"  {k} (dict): {list(v.keys())} -> {v.get('name') or v.get('title')}")
