import json
import sqlite3

# 1. Load the 37 Medway modules from HAR
with open("go_modules_raw.json", "r", encoding="utf-8") as f:
    medway_mods = json.load(f)

print(f"Medway GO modules: {len(medway_mods)}")

# 2. Load katomart
with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

# 3. Load local DB subtemas for GO
conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row
db_go = conn.execute("SELECT DISTINCT subtema FROM questions WHERE area LIKE '%Ginecologia%' OR area LIKE '%Obstetr%'").fetchall()
db_subtemas = [r["subtema"] for r in db_go]

print(f"Current DB GO subtemas: {len(db_subtemas)}")

# 4. Load focus data
with open("go_focus_sp.json", "r", encoding="utf-8") as f:
    sp = json.load(f)
with open("go_focus_rp.json", "r", encoding="utf-8") as f:
    rp = json.load(f)

sp_focos = {item["name"]: item for item in sp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")}
rp_focos = {item["name"]: item for item in rp if "Ginecologia" in item.get("discipline_name", "") or "Obstetr" in item.get("discipline_name", "")}

print("\n--- 37 Medway Modules Analysis ---")
for i, m in enumerate(medway_mods):
    name = m["name"]
    mid = m["id"]
    
    # Check katomart duration
    kat_match = kat.get("subtemas", {}).get(name)
    if not kat_match:
        for k, v in kat.get("subtemas", {}).items():
            if k.lower() in name.lower() or name.lower() in k.lower():
                kat_match = v
                break
                
    dur = kat_match.get("theory_hours") if kat_match else None
    
    # Check focus
    is_sp = name in sp_focos
    is_rp = name in rp_focos
    focus_str = ""
    if is_sp and is_rp: focus_str = "[FOCO: USP-SP + USP-RP]"
    elif is_sp: focus_str = "[FOCO: USP-SP]"
    elif is_rp: focus_str = "[FOCO: USP-RP]"
    
    # Check DB match
    db_match = [s for s in db_subtemas if s.lower() == name.lower()]
    
    print(f"[{i+1:02d}] {name} (ID: {mid}) | Dur: {dur}h | {focus_str} | DB: {len(db_match)} matches")
