import json

with open(r'C:\Users\wmors\Downloads\Clínica.har', 'r', encoding='utf-8') as f:
    data = json.load(f)

for e in data['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br/api/v2/lesson-subject/20365' in url:
        print(f"\nURL: {url}")
        text = e.get('response', {}).get('content', {}).get('text', '')
        if text:
            try:
                body = json.loads(text)
                print(f"Data snippet: {str(body)[:500]}")
                if isinstance(body, list):
                    for item in body:
                        if 'name' in item:
                            print(f"- {item.get('name')}: {item.get('estimated_time')}")
                elif isinstance(body, dict):
                    print(f"- {body.get('name')}")
            except Exception as ex:
                print(f"Error parsing json: {ex}")
