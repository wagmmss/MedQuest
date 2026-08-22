import json
import codecs
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
found = False
for i, entry in enumerate(har['log']['entries']):
    text = entry.get('response', {}).get('content', {}).get('text', '')
    if text and 'isqu' in text.lower():
        print(f"Match found in URL: {entry['request']['url']}")
        with open(f'medway_match_{i}.json', 'w', encoding='utf-8') as out:
            out.write(text)
        found = True
if not found:
    print("No matches found")
