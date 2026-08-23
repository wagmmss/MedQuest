import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open('ped_b1.json', encoding='utf-8') as f:
    batch = json.load(f)

print(f"Total: {len(batch)}")
for i, q in enumerate(batch):
    print(f"[{i:02d}] ID: {q['id']:<5} | Area: {q.get('current_area',''):<20} | Sub: {q.get('current_subtema','')[:45]:<45} | Topic: {str(q.get('topic',''))[:35]}")
