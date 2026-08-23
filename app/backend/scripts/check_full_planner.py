import urllib.request
import json
import uuid

guest = str(uuid.uuid4())

req = urllib.request.Request("http://127.0.0.1:5050/api/generate_plan", 
    data=json.dumps({"start_date": "2026-01-01", "exam_date": "2026-12-01", "hours_per_week": 20, "intensive": False}).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-Internal-Proxy-Token": "medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e", "X-Guest-ID": guest},
    method="POST")
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode("utf-8"))
plan = data.get("plan", [])

area_counts = {}
for w in plan:
    for t in w.get("topics", []):
        area = t.get("area", "Outros")
        area_counts[area] = area_counts.get(area, 0) + 1

print(f"Total Weeks: {len(plan)}")
print(f"Total Topics Scheduled: {sum(area_counts.values())}")
print("\nBreakdown by Area:")
for area, count in sorted(area_counts.items(), key=lambda x: x[1], reverse=True):
    print(f" - {area}: {count} topics")
