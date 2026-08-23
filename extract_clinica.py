import json

file_path = r'C:\Users\wmors\Downloads\Clínica Médica.har'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

clinica_themes = {}

for e in data['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br/api/v2/digital-mentoring/lesson-schedule' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            try:
                body = json.loads(text)
                for item in body:
                    # check if it belongs to Clínica Médica
                    if 'speciality_name' in item and item['speciality_name'] == 'Clínica Médica':
                        name = item.get('name')
                        if name:
                            # Time is in seconds.
                            time_hrs = item.get('estimated_time', 0) / 3600.0
                            priority = item.get('priority_level')
                            if name not in clinica_themes:
                                clinica_themes[name] = {'time': time_hrs, 'priority': priority}
            except Exception as ex:
                pass

print(f"Extracted {len(clinica_themes)} themes from Clínica Médica.")
for name, info in list(clinica_themes.items())[:10]:
    print(f"- {name}: {info['time']:.2f}h, Priority: {info['priority']}")

with open('clinica_summary.json', 'w', encoding='utf-8') as f:
    json.dump(clinica_themes, f, indent=2, ensure_ascii=False)
