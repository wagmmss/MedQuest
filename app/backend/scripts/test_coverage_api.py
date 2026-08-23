import urllib.request
import json
import uuid

guest = str(uuid.uuid4())
req = urllib.request.Request("http://127.0.0.1:5050/api/coverage", 
    headers={"X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode("utf-8"))

print(f"Coverage returned {len(data.get('areas', []))} areas:")
for a in data.get("areas", []):
    print(f"\nArea: {a['area']} | Questions: {a['n_questions']} | Subtemas: {a['n_subtemas']}")
    print("First 5 subtemas:")
    for s in a["subtemas"][:5]:
        print(f"  - {s['subtema']}: {s['n_questions']} questions")
