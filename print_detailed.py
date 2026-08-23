import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

def print_detailed(start, end):
    with open('ped_b1.json', encoding='utf-8') as f:
        batch = json.load(f)
    for i in range(start, min(end, len(batch))):
        q = batch[i]
        print("="*60)
        print(f"[{i}] ID: {q['id']} | Current: {q.get('current_area')} -> {q.get('current_subtema')}")
        print(f"Topic: {q.get('topic')}")
        print(f"Stem:\n{q.get('stem')}\n")
        print(f"Alternatives:\n{q.get('alternatives')}\n")
        print(f"Explanation:\n{q.get('explanation')}\n")

if __name__ == "__main__":
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    e = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print_detailed(s, e)
