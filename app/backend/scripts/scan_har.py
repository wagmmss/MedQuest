import json

har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

for i, e in enumerate(har['log']['entries']):
    url = e['request']['url']
    text = e.get('response', {}).get('content', {}).get('text', '')
    if not text:
        continue
    # Check if there are other courses or subjects
    if 'Extensivo' in text or 'Cirurgia' in text or 'Clínica' in text or 'Pediatria' in text or 'Preventiva' in text:
        print(f"Entry {i}: {url[:100]} | Length: {len(text)}")
        try:
            d = json.loads(text)
            if isinstance(d, list):
                print(f"  List of {len(d)} items. Sample: {str(d[0])[:150]}")
            elif isinstance(d, dict):
                print(f"  Dict keys: {list(d.keys())[:10]}")
        except Exception:
            pass
