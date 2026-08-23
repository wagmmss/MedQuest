import sys

with open('app/backend/api/plan.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'rows = db.execute(q_query).fetchall()\n    a_query =',
    'rows = [dict(r) for r in db.execute(q_query).fetchall()]\n    a_query ='
)

content = content.replace(
    'answered = db.execute(a_query, (g.user_id,)).fetchall()\n    answered_map = {r["subtema"]: r for r in answered}',
    'answered = db.execute(a_query, (g.user_id,)).fetchall()\n    answered_map = {r["subtema"]: dict(r) for r in answered}'
)

with open('app/backend/api/plan.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced!")
