import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
for e in har['log']['entries']:
    url = e['request']['url']
    if 'medway.com.br' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text and len(text) > 100:
            if 'Abdome' in text or 'Isqu' in text or 'AVC' in text or 'avc' in text:
                print(url)
