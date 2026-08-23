import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open('cir_b1.json', encoding='utf-8') as f:
    qs = json.load(f)

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 25

for i in range(start, min(end, len(qs))):
    q = qs[i]
    print(f"=== [{i}] ID: {q['id']} ===")
    print(f"Current: Area='{q.get('current_area')}' | Subtema='{q.get('current_subtema')}' | Topic='{q.get('topic')}'")
    print("STEM:", q['stem'])
    print("ALTS:", q.get('alternatives'))
    print("EXP:", q.get('explanation', '')[:300])
    print()
