import json
har_path = r'C:\Users\wmors\Downloads\app.medway.com.br.har'
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)
found_urls = []
for i, entry in enumerate(har['log']['entries']):
    text = entry.get('response', {}).get('content', {}).get('text', '')
    if text and ('perfurativo' in text.lower() or 'hemorrágico' in text.lower() or 'hemorragico' in text.lower()):
        url = entry['request']['url']
        if url not in found_urls:
            print(f"Match found in URL: {url}")
            found_urls.append(url)
            with open(f'medway_struct_{len(found_urls)}.json', 'w', encoding='utf-8') as out:
                out.write(text)
