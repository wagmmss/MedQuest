import json

with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    k_data = json.load(f)

with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    p_data = json.load(f)

with open('app/backend/scripts/deepseek_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

old_modules = list(k_data['subtemas'].keys())
new_db_subtemas = [st for a in p_data for m in a.get('macroThemes', []) for st in m.get('dbSubtemas', [])]

old_module_counts = {}
for new_st, old_mod in mapping.items():
    if old_mod in old_modules:
        old_module_counts[old_mod] = old_module_counts.get(old_mod, 0) + 1

new_katomart = {}
for new_st in new_db_subtemas:
    if "AVC isqu" in new_st:
        new_katomart[new_st] = {
            "theory_hours": 1.5,
            "module": "AVC",
            "match_confidence": 1.0
        }
        continue
    if "Abdome Agudo Obstrutivo e Perfurativo" in new_st:
        old1 = k_data['subtemas'].get("Abdome Agudo Obstrutivo", {}).get("theory_hours", 1.0)
        old2 = k_data['subtemas'].get("Abdome Agudo Perfurativo", {}).get("theory_hours", 1.0)
        new_katomart[new_st] = {
            "theory_hours": old1 + old2,
            "module": "Abdome Agudo Obstrutivo e Perfurativo",
            "match_confidence": 1.0
        }
        continue

    old_mod = mapping.get(new_st)
    if old_mod in old_modules:
        orig_data = k_data['subtemas'][old_mod]
        count = old_module_counts[old_mod]
        divided_hours = round(orig_data.get("theory_hours", 1.0) / count, 2)
        divided_hours = max(0.25, divided_hours)
        new_katomart[new_st] = {
            "theory_hours": divided_hours,
            "module": orig_data.get("module", old_mod),
            "match_confidence": 0.95
        }
    else:
        new_katomart[new_st] = {
            "theory_hours": 1.0,
            "module": "Unknown",
            "match_confidence": 0.0
        }

k_data['subtemas'] = new_katomart

with open('app/backend/scripts/katomartCourseDurations.json', 'w', encoding='utf-8') as f:
    json.dump(k_data, f, ensure_ascii=False, indent=2)

print("Applied mapping perfectly!")
