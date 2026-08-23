import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

print(f"Total areas in taxonomy.json: {len(tax)}")
for i, a in enumerate(tax):
    print(f"[{i+1}] '{a.get('area')}' -> {len(a.get('macroThemes', []))} macroThemes")
