import json

with open('medway_modules.json', 'r', encoding='utf-8') as f:
    mods = json.load(f)

print("First module structure:")
print(json.dumps(mods[0], indent=2, ensure_ascii=False))
