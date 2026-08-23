import json

har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

for i, e in enumerate(har['log']['entries']):
    url = e['request']['url']
    text = e.get('response', {}).get('content', {}).get('text', '')
    if 'medway.com.br' in url and text:
        try:
            d = json.loads(text)
            print(f"\n--- Entry {i}: {url} ---")
            if isinstance(d, list):
                print(f"List of {len(d)} items")
                if len(d) > 0 and isinstance(d[0], dict):
                    print(f"Item 0 keys: {list(d[0].keys())}")
                    if 'name' in d[0]:
                        print(f"Names: {[x.get('name') for x in d[:5]]}")
            elif isinstance(d, dict):
                print(f"Dict keys: {list(d.keys())}")
                if 'name' in d:
                    print(f"Name: {d.get('name')}")
        except Exception:
            pass
