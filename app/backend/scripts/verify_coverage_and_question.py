import urllib.request
import json
import uuid

guest = str(uuid.uuid4())

print("Testing GET /api/coverage...")
req = urllib.request.Request("http://127.0.0.1:5050/api/coverage", 
    headers={"X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode("utf-8"))
print(f"Coverage status: {resp.status} | Areas: {len(data.get('areas', []))}")
for a in data.get("areas", []):
    print(f" - {a['area']}: {a['n_subtemas']} subtemas | {a['n_questions']} questions | {a['high_yield_count']} high-yield")

print("\nTesting GET /api/questions/3282...")
req = urllib.request.Request("http://127.0.0.1:5050/api/questions/3282", 
    headers={"X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest})
resp = urllib.request.urlopen(req)
q_data = json.loads(resp.read().decode("utf-8"))
print(f"Question status: {resp.status} | Topic: {q_data.get('topic')} | Subtema: {q_data.get('subtema')}")

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
