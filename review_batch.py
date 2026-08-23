import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open('cir_b1.json', encoding='utf-8') as f:
    qs = json.load(f)

def print_batch(start, end):
    for i in range(start, end):
        q = qs[i]
        print(f"=== [{i}] ID: {q['id']} ===")
        print(f"CURRENT: Area='{q.get('current_area')}' | Subtema='{q.get('current_subtema')}' | Topic='{q.get('topic')}'")
        print("STEM:", q['stem'].strip())
        print("ALTS:", json.dumps(q.get('alternatives', []), ensure_ascii=False))
        print("EXP:", q.get('explanation', '').strip()[:350])
        print()

if __name__ == '__main__':
    s = int(sys.argv[1])
    e = int(sys.argv[2])
    print_batch(s, e)
