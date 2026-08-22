import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
for e in har['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br/api' in url:
        print(f"\n--- URL: {url} ---")
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            print(text[:200] + '...')
