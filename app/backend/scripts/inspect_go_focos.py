import json

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)

with open("go_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

print("=== USP-SP (Institution 26) - Ginecologia e Obstetrícia ===")
sp_go = [item for item in sp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")]
for item in sorted(sp_go, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min questions: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print(f"\nTotal USP-SP GO Focos: {len(sp_go)}")

print("\n=== USP-RP (Institution 27) - Ginecologia e Obstetrícia ===")
rp_go = [item for item in rp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")]
for item in sorted(rp_go, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min questions: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print(f"\nTotal USP-RP GO Focos: {len(rp_go)}")
