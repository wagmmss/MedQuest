import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

def print_detailed(start, count):
    with open('cir_b1.json', encoding='utf-8') as f:
        qs = json.load(f)
    
    end = min(start + count, len(qs))
    for i in range(start, end):
        q = qs[i]
        print(f"[{i}] ID: {q['id']}")
        print(f"Current: Area='{q.get('current_area')}', Subtema='{q.get('current_subtema')}', Topic='{q.get('topic')}'")
        print(f"STEM: {q['stem']}")
        print("ALTS:", json.dumps(q.get('alternatives', []), ensure_ascii=False))
        exp = q.get('explanation', '')
        # print first 250 chars of explanation
        print(f"EXP: {exp[:300]}...")
        print("-" * 60)

if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    c = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print_detailed(s, c)
