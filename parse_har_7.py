import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
for e in har['log']['entries']:
    text = e.get('response', {}).get('content', {}).get('text', '')
    if text and ('isqu' in text.lower() or 'perfurativo' in text.lower()):
        print(f"Found in URL: {e['request']['url']}")
