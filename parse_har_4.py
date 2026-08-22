import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
for e in har['log']['entries']:
    url = e['request']['url']
    if 'modules' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text and text.startswith('['):
            with open('medway_modules.json', 'w', encoding='utf-8') as out:
                out.write(text)
            print("Dumped medway_modules.json")
