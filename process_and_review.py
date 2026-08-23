import json
import sys
from classify_engine import classify_question

sys.stdout.reconfigure(encoding="utf-8")

with open('canonical_taxonomy_170.json', encoding='utf-8') as f:
    tax = json.load(f)

valid_themes = {}
for area, themes in tax.items():
    for t in themes:
        valid_themes[t] = area

def run_batch(input_file, output_file):
    with open(input_file, encoding='utf-8') as f:
        qs = json.load(f)
    
    if not qs:
        print(f"{input_file} has 0 questions.")
        return 0
    
    results = []
    changes = 0
    for i, q in enumerate(qs):
        target_area, target_subtema, rationale = classify_question(q)
        
        # Verify valid
        if target_subtema not in valid_themes or valid_themes[target_subtema] != target_area:
            print(f"ERROR on QID {q['id']}: {target_area} -> {target_subtema} is invalid!")
            sys.exit(1)
        
        if q['current_subtema'] != target_subtema or q['current_area'] != target_area:
            changes += 1
            print(f"[{i:02d}] ID {q['id']}: [{q['current_area']} | {q['current_subtema']}] -> [{target_area} | {target_subtema}]")
            print(f"    Topic: {q.get('topic')}")
            print(f"    Stem: {q['stem'][:140]}...")
            print(f"    Rationale: {rationale}")
            print("-" * 50)
            
        results.append({
            "id": q['id'],
            "target_area": target_area,
            "target_subtema": target_subtema,
            "confidence": 1.0,
            "rationale": rationale
        })
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\nTotal questions: {len(results)} | Reclassifications/Fixes: {changes}")
    print(f"Saved {output_file} successfully.")
    return len(results)

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else 'cir_b2.json'
    out = sys.argv[2] if len(sys.argv) > 2 else 'cir_b2_classified.json'
    run_batch(inp, out)
