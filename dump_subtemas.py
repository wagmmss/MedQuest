import json
with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
cirurgia = next((a for a in data if a['area'] == 'Cirurgia Geral'), None)
old_subtemas = []
if cirurgia:
    for m in cirurgia['macroThemes']:
        for s in m['dbSubtemas']:
            old_subtemas.append(s)

with open('old_cirurgia_subtemas.json', 'w', encoding='utf-8') as f:
    json.dump(old_subtemas, f, indent=2, ensure_ascii=False)
