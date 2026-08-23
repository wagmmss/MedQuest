import json

with open("preventiva_modules_raw.json", "r", encoding="utf-8") as f:
    modules = json.load(f)

print(f"Total Medway Preventiva Modules: {len(modules)}")

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)

with open("pediatria_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_prev = [item for item in sp if "Preventiva" in item.get("discipline_name", "") or "Social" in item.get("discipline_name", "")]
rp_prev = [item for item in rp if "Preventiva" in item.get("discipline_name", "") or "Social" in item.get("discipline_name", "")]

print(f"\n--- USP-SP Focos (Preventiva: {len(sp_prev)}) ---")
for item in sorted(sp_prev, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print(f"\n--- USP-RP Focos (Preventiva: {len(rp_prev)}) ---")
for item in sorted(rp_prev, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print("\n--- 13 Medway Preventiva Modules ---")
for i, m in enumerate(modules):
    print(f"[{i+1:02d}] ID: {m.get('id')} | Name: {m.get('name')}")
