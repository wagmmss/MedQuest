import json

har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

for i, e in enumerate(har['log']['entries']):
    url = e['request']['url']
    text = e.get('response', {}).get('content', {}).get('text', '')
    if 'lesson-subject' in url:
        print(f"URL: {url}")
        print(f"Snippet: {text[:200]}...")
