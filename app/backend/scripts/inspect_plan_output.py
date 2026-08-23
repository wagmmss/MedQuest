import sys
sys.path.insert(0, 'app/backend')
from app import create_app
import uuid

app = create_app()
app.config['TESTING'] = True
client = app.test_client()

guest_id = str(uuid.uuid4())
headers = {
    'X-Guest-ID': guest_id,
    'X-Internal-Proxy-Token': 'medquest-local-7f9c2d4e8a1b6c3f5d0e9a2b4c7f8d1e',
    'Content-Type': 'application/json'
}

client.post('/api/planner/config', headers=headers, json={'exam_date': '2026-12-01', 'start_date': '2026-01-01', 'days_per_week': 5, 'hours_per_day': 4, 'target_score': 80})
r = client.post('/api/generate_plan', headers=headers, json={'start_date': '2026-01-01', 'exam_date': '2026-12-01', 'hours_per_week': 20, 'intensive': False})
plan = r.get_json()['plan']

all_topics = []
for w in plan:
    for t in w['topics']:
        all_topics.append(f"{t['area']} -> {t['subtema']} ({t.get('course_module', 'Sem módulo')}) | Teoria: {t.get('theory_hours', 0)}h | Questões: {t.get('q_count', 0)}")

print(f"Total topics in plan: {len(all_topics)}")
for t in all_topics[:25]:
    print(t)
