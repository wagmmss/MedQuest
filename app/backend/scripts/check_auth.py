import json

har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

for e in har['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br' in url:
        headers = {h['name']: h['value'] for h in e['request']['headers']}
        print(f"URL: {url}")
        print("Headers:", {k: v for k, v in headers.items() if k.lower() in ['authorization', 'token', 'cookie']})
        break
