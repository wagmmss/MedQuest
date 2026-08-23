import json
import re

file_path = r'C:\Users\wmors\Downloads\Clínica Médica.har'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data['log']['entries'])}")

has_schedule = False
has_focus = False

schedule_count = 0
focus_count = 0

for e in data['log']['entries']:
    url = e['request']['url']
    text = e.get('response', {}).get('content', {}).get('text', '')
    
    if 'lesson-schedule' in url and 'estimated_time' in text:
        has_schedule = True
        try:
            body = json.loads(text)
            schedule_count += len(body)
        except:
            pass

    # Medway usually puts focus in `goal-institutions-priority` or `focus` endpoints
    if 'focus' in url or 'priority' in url or 'USP' in text or 'usp' in text.lower():
        if 'focus' in text or 'priority' in text:
            # Let's just check if it contains a list of themes
            if 'Saúde Mental' in text or 'Insuficiência' in text:
                has_focus = True
                focus_count += 1

print(f"Has schedule (durations)? {has_schedule} ({schedule_count} items)")
print(f"Has focus? {has_focus} ({focus_count} endpoints matched)")
