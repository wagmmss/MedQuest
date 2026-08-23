import json
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open('ped_b1.json', encoding='utf-8') as f:
    batch = json.load(f)

print(f"Total questions in ped_b1.json: {len(batch)}")

for idx, q in enumerate(batch):
    print(f"\n==================== INDEX {idx} | ID {q['id']} ====================")
    print(f"TOPIC: {q.get('topic')}")
    print(f"CURRENT: {q.get('current_area')} -> {q.get('current_subtema')}")
    print(f"STEM:\n{q.get('stem')}")
    print(f"ALTS:\n{q.get('alternatives')}")
    print(f"EXPL:\n{q.get('explanation')[:400]}")
