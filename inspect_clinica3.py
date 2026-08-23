import json

with open(r'C:\Users\wmors\Downloads\Clínica.har', 'r', encoding='utf-8') as f:
    data = json.load(f)

for e in data['log']['entries']:
    url = e['request']['url']
    if 'cms.medway.com.br/api/v2/lesson-subject/20365/modules' in url:
        text = e.get('response', {}).get('content', {}).get('text', '')
        body = json.loads(text)
        print(json.dumps(body[0], indent=2, ensure_ascii=False))
        break
