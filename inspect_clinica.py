import json

with open(r'C:\Users\wmors\Downloads\Clínica.har', 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data['log']['entries']
print(f"Total entries: {len(entries)}")

endpoints = set()
for i, e in enumerate(entries):
    url = e['request']['url']
    if 'medway' in url or 'cms' in url:
        base = url.split('?')[0]
        endpoints.add(base)

for ep in sorted(endpoints):
    print(f"  {ep}")

# Find endpoints with 'schedule' or 'focus' or 'modules'
for i, e in enumerate(entries):
    url = e['request']['url']
    if 'schedule' in url or 'focus' in url or 'modules' in url:
        resp = e.get('response', {})
        content = resp.get('content', {})
        text = content.get('text', '')
        if text:
            print(f"\nFound relevant data at: {url}")
            try:
                body = json.loads(text)
                if isinstance(body, list) and len(body) > 0:
                    print(f"List of {len(body)} items")
                    print(f"Keys of first item: {list(body[0].keys())}")
                elif isinstance(body, dict):
                    print(f"Dict keys: {list(body.keys())}")
                    if 'data' in body and isinstance(body['data'], list):
                        print(f"Data list of {len(body['data'])} items")
                        if len(body['data']) > 0:
                            print(f"Keys of first item in data: {list(body['data'][0].keys())}")
            except Exception as ex:
                print(f"Error parsing json: {ex}")
