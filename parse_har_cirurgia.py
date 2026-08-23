"""Inspect raw content of Cirurgia FOCOS.har entries."""
import json

with open(r'C:\Users\wmors\Downloads\Cirurgia FOCOS.har', 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data['log']['entries']
print(f"Total entries: {len(entries)}")

for i, e in enumerate(entries):
    url = e['request']['url']
    method = e['request']['method']
    resp = e.get('response', {})
    status = resp.get('status', 0)
    content = resp.get('content', {})
    mime = content.get('mimeType', '')
    size = content.get('size', 0)
    text = content.get('text', '')
    
    print(f"\n--- Entry {i} ---")
    print(f"  {method} {url[:200]}")
    print(f"  Status: {status} | MIME: {mime} | Size: {size}")
    
    if text:
        # Show first 500 chars of text
        preview = text[:500].replace('\n', '\\n')
        print(f"  Body preview: {preview}")
    else:
        print(f"  No text body")
    
    # Check for post data
    post_data = e['request'].get('postData', {})
    if post_data:
        post_mime = post_data.get('mimeType', '')
        post_text = post_data.get('text', '')
        print(f"  POST data MIME: {post_mime}")
        if post_text:
            preview = post_text[:500].replace('\n', '\\n')
            print(f"  POST data preview: {preview}")
