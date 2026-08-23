import json

with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    p = json.load(f)
    
with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    k = json.load(f)

# The area is "Clínica Médica"
cm = next(a for a in p if a['area'] == 'Clínica Médica')

res = []
total_h = 0
for m in cm['macroThemes']:
    r = {'theme': m['theme'], 'subtemas': []}
    for st in m['dbSubtemas']:
        h = k['subtemas'].get(st, {}).get('theory_hours', 1.0)
        total_h += h
        r['subtemas'].append({'name': st, 'hours': h, 'details_count': len(m.get('details', []))})
    res.append(r)

print(f"Total Hours CM: {total_h:.2f}")
print(json.dumps(res, indent=2, ensure_ascii=False))
