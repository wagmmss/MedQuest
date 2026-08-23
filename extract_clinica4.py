import json
import unidecode
import re

file_path = r'C:\Users\wmors\Downloads\Clínica Médica.har'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. Get all Clinica Medica theme names from the modules endpoint
clinica_theme_names = set()
for e in data['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br/api/v2/lesson-subject/20365/modules/' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            try:
                body = json.loads(text)
                for item in body:
                    if 'name' in item:
                        clinica_theme_names.add(item['name'])
            except: pass

# 2. Get focuses for USP-SP (27) and USP-RP (26)
foco_themes = set()
for e in data['log']['entries']:
    url = e['request']['url']
    if 'medbrain/student-domain/focus' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            try:
                body = json.loads(text)
                for item in body:
                    if item.get('discipline_name') == 'Clínica Médica':
                        foco_themes.add(item.get('name'))
            except: pass

# 3. Sum times from lesson-schedule for those themes
clinica_themes = {}
for e in data['log']['entries']:
    url = e['request']['url']
    if 'lesson-schedule' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            try:
                body = json.loads(text)
                items = body.get('items', [])
                for item in items:
                    theme_name = item.get('object_name')
                    if theme_name in clinica_theme_names:
                        content_type = item.get('content_type')
                        time_str = item.get('estimated_time')
                        try:
                            time_sec = float(time_str) if time_str else 0.0
                        except:
                            time_sec = 0.0
                        
                        if theme_name not in clinica_themes:
                            clinica_themes[theme_name] = {'lesson_hours': 0.0, 'practice_hours': 0.0, 'total_hours': 0.0, 'highYield': False}
                        
                        clinica_themes[theme_name]['total_hours'] += time_sec / 3600.0
                        
                        if content_type in ['lesson', 'chapter', 'lessondocument']:
                            clinica_themes[theme_name]['lesson_hours'] += time_sec / 3600.0
                        elif content_type == 'track' and 'pós' in item.get('name', '').lower():
                            clinica_themes[theme_name]['practice_hours'] += time_sec / 3600.0
            except: pass

# Combine 'Como cai' into parent theme
final_themes = {}
for name, data_item in clinica_themes.items():
    base_name = name.split(': ')[-1] if 'Como cai' in name else name
    if base_name not in final_themes:
        final_themes[base_name] = {'lesson_hours': 0.0, 'practice_hours': 0.0, 'total_hours': 0.0, 'highYield': False}
    
    final_themes[base_name]['lesson_hours'] += data_item['lesson_hours']
    final_themes[base_name]['practice_hours'] += data_item['practice_hours']
    final_themes[base_name]['total_hours'] += data_item['total_hours']

# Flag highYield
for base_name in final_themes:
    # try direct match
    if base_name in foco_themes:
        final_themes[base_name]['highYield'] = True
    else:
        # maybe encoding or slight differences
        for f in foco_themes:
            if unidecode.unidecode(f.lower()) == unidecode.unidecode(base_name.lower()):
                final_themes[base_name]['highYield'] = True

with open('clinica_summary.json', 'w', encoding='utf-8') as f:
    json.dump(final_themes, f, indent=2, ensure_ascii=False)
