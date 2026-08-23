import json
import difflib

def normalize(s):
    return s.lower()

with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    k_data = json.load(f)

with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    p_data = json.load(f)

old_subtemas = list(k_data['subtemas'].keys())
new_db_subtemas = [st for a in p_data for m in a.get('macroThemes', []) for st in m.get('dbSubtemas', [])]

new_katomart = {}

for new_st in new_db_subtemas:
    # Special cases
    if "AVC isqu" in new_st:
        new_katomart[new_st] = {
            "theory_hours": 1.5,  # User explicitly requested ~1.5h
            "module": "AVC",
            "match_confidence": 1.0
        }
        continue
    if "Abdome Agudo Obstrutivo e Perfurativo" in new_st:
        # Sum of both
        old1 = k_data['subtemas'].get("Abdome Agudo Obstrutivo", {}).get("theory_hours", 1.0)
        old2 = k_data['subtemas'].get("Abdome Agudo Perfurativo", {}).get("theory_hours", 1.0)
        new_katomart[new_st] = {
            "theory_hours": old1 + old2,
            "module": "Abdome Agudo Obstrutivo e Perfurativo",
            "match_confidence": 1.0
        }
        continue

    # Auto-match
    matches = difflib.get_close_matches(new_st, old_subtemas, n=1, cutoff=0.3)
    if not matches:
        # Try finding old substring in new
        for old in old_subtemas:
            if normalize(old) in normalize(new_st) or normalize(new_st) in normalize(old):
                matches = [old]
                break

    if matches:
        best = matches[0]
        # Keep old data but mapped to new string
        new_katomart[new_st] = k_data['subtemas'][best]
    else:
        # Default
        new_katomart[new_st] = {
            "theory_hours": 1.0,
            "module": "Unknown",
            "match_confidence": 0.0
        }

k_data['subtemas'] = new_katomart

with open('app/backend/scripts/katomartCourseDurations.json', 'w', encoding='utf-8') as f:
    json.dump(k_data, f, ensure_ascii=False, indent=2)

print("Mapping complete. Keys updated to match plannerData.json.")
