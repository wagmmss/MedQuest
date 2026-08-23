import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

def show(filename, start, count):
    with open(filename, encoding='utf-8') as f:
        qs = json.load(f)
    end = min(start + count, len(qs))
    print(f"Total in {filename}: {len(qs)}. Showing {start} to {end-1}:")
    for i in range(start, end):
        q = qs[i]
        print(f"=== [{i:02d}] ID: {q['id']} ===")
        print(f"Curr: Area='{q.get('current_area')}' | Subtema='{q.get('current_subtema')}' | Topic='{q.get('topic')}'")
        print("STEM:", q['stem'].strip()[:250], "..." if len(q['stem']) > 250 else "")
        print("ALTS:", q.get('alternatives', '').strip())
        print("EXP:", q.get('explanation', '').strip()[:250])
        print()

if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv) > 1 else 'cir_b2.json'
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    c = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    show(fn, s, c)
