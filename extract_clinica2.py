import json

file_path = r'C:\Users\wmors\Downloads\Clínica Médica.har'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

clinica_themes = {}
high_yield_themes = set()
medium_yield_themes = set()

for e in data['log']['entries']:
    url = e['request']['url']
    text = e.get('response', {}).get('content', {}).get('text', '')
    
    # 1. Extract focus / priority
    if 'medbrain/student-domain/rocket/?priority_level=p' in url and text:
        try:
            body = json.loads(text)
            for item in body:
                if item.get('speciality_name') == 'Clínica Médica':
                    name = item.get('name')
                    if name:
                        # Extract base name without 'Como cai' for mapping
                        base_name = name.split(': ')[-1] if 'Como cai' in name else name
                        high_yield_themes.add(base_name)
        except: pass
    
    # Extract medium priority just in case
    if 'medbrain/student-domain/rocket/?priority_level=h' in url and text:
        try:
            body = json.loads(text)
            for item in body:
                if item.get('speciality_name') == 'Clínica Médica':
                    name = item.get('name')
                    if name:
                        base_name = name.split(': ')[-1] if 'Como cai' in name else name
                        medium_yield_themes.add(base_name)
        except: pass

    # 2. Extract lesson schedules (time)
    if 'lesson-schedule' in url and 'estimated_time' in text:
        try:
            body = json.loads(text)
            items = body.get('items', [])
            for item in items:
                # Group by object_name (the theme)
                theme_name = item.get('object_name')
                if not theme_name: continue
                
                content_type = item.get('content_type')
                time_str = item.get('estimated_time')
                try:
                    time_sec = float(time_str) if time_str else 0.0
                except:
                    time_sec = 0.0
                
                if theme_name not in clinica_themes:
                    clinica_themes[theme_name] = {'lesson_hours': 0.0, 'total_hours': 0.0, 'practice_hours': 0.0}
                
                clinica_themes[theme_name]['total_hours'] += time_sec / 3600.0
                
                if content_type == 'lesson':
                    clinica_themes[theme_name]['lesson_hours'] += time_sec / 3600.0
                elif content_type == 'track' and 'pós' in item.get('name', '').lower():
                    clinica_themes[theme_name]['practice_hours'] += time_sec / 3600.0
                    
        except Exception as ex:
            pass

print(f"Extracted {len(clinica_themes)} themes from Clínica Médica.")
print(f"High Yield (FOCO USP): {len(high_yield_themes)} themes")
print(f"Medium Yield: {len(medium_yield_themes)} themes")

# Combine 'Como cai' into parent theme
final_themes = {}
for name, data in clinica_themes.items():
    base_name = name.split(': ')[-1] if 'Como cai' in name else name
    if base_name not in final_themes:
        final_themes[base_name] = {'lesson_hours': 0.0, 'total_hours': 0.0, 'highYield': False}
    
    final_themes[base_name]['lesson_hours'] += data['lesson_hours']
    final_themes[base_name]['total_hours'] += data['total_hours']
    
    if base_name in high_yield_themes:
        final_themes[base_name]['highYield'] = True

print(f"\nFinal grouped themes: {len(final_themes)}")
for name, data in list(final_themes.items())[:5]:
    print(f"- {name}: {data['lesson_hours']:.2f}h lessons (Total: {data['total_hours']:.2f}h) [FOCO: {data['highYield']}]")

with open('clinica_summary.json', 'w', encoding='utf-8') as f:
    json.dump(final_themes, f, indent=2, ensure_ascii=False)
