import json

with open("pediatria_modules_raw.json", "r", encoding="utf-8") as f:
    modules = json.load(f)

print(f"Total Medway Pediatria Modules: {len(modules)}")

with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)

with open("pediatria_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_ped = [item for item in sp if "Pediatria" in item.get("discipline_name", "")]
rp_ped = [item for item in rp if "Pediatria" in item.get("discipline_name", "")]

print(f"\n--- USP-SP Focos (Pediatria: {len(sp_ped)}) ---")
for item in sorted(sp_ped, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print(f"\n--- USP-RP Focos (Pediatria: {len(rp_ped)}) ---")
for item in sorted(rp_ped, key=lambda x: x.get("score_rf", 0), reverse=True):
    print(f" - [{item.get('score_rf', 0):.3f}] {item.get('name')} (Theme: {item.get('theme_name')}) | Min: {item.get('offset_min')} | Avail: {item.get('available_questions')}")

print("\n--- 30 Medway Pediatria Modules ---")
for i, m in enumerate(modules):
    print(f"[{i+1:02d}] ID: {m.get('id')} | Name: {m.get('name')}")
