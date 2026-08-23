import json

har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

print(f"Total entries: {len(har['log']['entries'])}")

json_responses = []
for i, e in enumerate(har['log']['entries']):
    url = e['request']['url']
    mime = e.get('response', {}).get('content', {}).get('mimeType', '')
    text = e.get('response', {}).get('content', {}).get('text', '')
    if 'json' in mime or (text.startswith('{') or text.startswith('[')):
        try:
            data = json.loads(text)
            json_responses.append((i, url, type(data), len(str(data))))
        except Exception:
            pass

print(f"Found {len(json_responses)} JSON responses")
for idx, url, dtype, length in json_responses[:50]:
    print(f"[{idx}] {url} -> {dtype} ({length} chars)")
