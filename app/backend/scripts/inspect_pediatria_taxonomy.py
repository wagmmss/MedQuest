import json

with open('app/backend/data/taxonomy.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

for a in tax:
    if a['area'] == 'Pediatria':
        for m in a['macroThemes']:
            print(f"THEME: {m['theme']}")
            print(f"  dbSubtemas: {m.get('dbSubtemas', [])}")
            print(f"  details: {m.get('details', [])}")
            print()
