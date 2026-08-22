import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
urls = set()
for e in har['log']['entries']:
    url = e['request']['url']
    if 'medway.com.br/api' in url:
        urls.add(url.split('?')[0])
for u in sorted(urls): print(u)
