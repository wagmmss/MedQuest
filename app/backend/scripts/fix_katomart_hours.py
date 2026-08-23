import json
import difflib

# Load current data
with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    k_data = json.load(f)

with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    p_data = json.load(f)

# Extract new dbSubtemas
new_db_subtemas = []
for area in p_data:
    for macro in area.get('macroThemes', []):
        new_db_subtemas.extend(macro.get('dbSubtemas', []))

print(f"Total new dbSubtemas: {len(new_db_subtemas)}")

# Map old keys to new dbSubtemas
old_keys = list(k_data['subtemas'].keys())
new_mapping = {}

for new_st in new_db_subtemas:
    # Find all old keys that are substrings of the new string (e.g. "AVC e Doenças..." in "AVC isquêmico...")
    # Or use difflib to find the best match
    
    # We can use difflib get_close_matches
    matches = difflib.get_close_matches(new_st, old_keys, n=3, cutoff=0.3)
    
    # Special cases
    if "AVC" in new_st:
        matches = [k for k in old_keys if "AVC" in k]
    if "Abdome Agudo Obstrutivo" in new_st:
        matches = [k for k in old_keys if "Abdome Agudo" in k and ("Obstrutivo" in k or "Perfurativo" in k)]
    
    # Aggregate hours for all matches?
    # Actually, it's better to assign the hours to the NEW key based on the OLD keys that best match it.
    
    # Let's map it manually for the ones the user complained about, or do it comprehensively.
    
    # For now, let's just collect the most likely old keys for each new_st
    pass

# Wait! The easiest way is to re-run the Katomart extraction script against the NEW `questions` table!
# Because the Katomart extraction script matched `questions` subtemas to the Katomart catalog!
# Is there an extraction script?
