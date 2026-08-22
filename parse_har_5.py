import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
count = 0
for e in har['log']['entries']:
    url = e['request']['url']
    if 'modules' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text and text.startswith('['):
            with open(f'medway_modules_{count}.json', 'w', encoding='utf-8') as out:
                out.write(text)
            count += 1
print(f"Dumped {count} module files")
