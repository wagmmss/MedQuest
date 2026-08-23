import urllib.request
import json
import uuid

guest = str(uuid.uuid4())

print("1. Testing POST /api/planner/config...")
req = urllib.request.Request("http://127.0.0.1:5050/api/planner/config", 
    data=json.dumps({"exam_date": "2026-12-01", "start_date": "2026-01-01", "days_per_week": 5, "hours_per_day": 4, "target_score": 80}).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest},
    method="POST")
resp = urllib.request.urlopen(req)
print("Config status:", resp.status, resp.read().decode())

print("\n2. Testing POST /api/generate_plan...")
req = urllib.request.Request("http://127.0.0.1:5050/api/generate_plan", 
    data=json.dumps({"start_date": "2026-01-01", "exam_date": "2026-12-01", "hours_per_week": 20, "intensive": False}).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest},
    method="POST")
resp = urllib.request.urlopen(req)
print("Generate status:", resp.status)
data = json.loads(resp.read().decode("utf-8"))
plan = data.get("plan", [])
print("Total weeks in plan:", len(plan))

ped_topics = []
for w in plan:
    for t in w.get("topics", []):
        if t.get("area") == "Pediatria":
            ped_topics.append(t)

print(f"\nTotal Pediatria topics in plan: {len(ped_topics)}")
for i, t in enumerate(ped_topics):
    hy = "🔥 High-Yield" if t.get("highYield") else ""
    print(f"[{i+1:02d}] {t['subtema']} | Module: {t.get('course_module')} | Theory: {t.get('theory_hours')}h | Total: {t.get('estimated_hours')}h | Qs: {t.get('q_count')} {hy}")

assert len(ped_topics) == 28, f"Expected 28 Pediatria topics in plan, got {len(ped_topics)}"
print("\n>>> ALL 28 PEDIATRIA MODULES VERIFIED PERFECTLY IN PLAN! <<<")
