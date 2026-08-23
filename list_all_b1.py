import json

with open('canonical_taxonomy_170.json', encoding='utf-8') as f:
    tax = json.load(f)

valid_themes = {}
for area, themes in tax.items():
    for t in themes:
        valid_themes[t] = area

with open('cir_b1.json', encoding='utf-8') as f:
    qs = json.load(f)

print(f"Total questions loaded: {len(qs)}")
for i, q in enumerate(qs):
    print(f"[{i:02d}] ID: {q['id']} | Current Area: {q['current_area']} | Subtema: {q['current_subtema']} | Topic: {q.get('topic')}")
