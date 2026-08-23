import json
import requests

def call_deepseek(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-2dc9602f50834037a65e670c2d4aada0"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a medical curriculum expert. You must map highly granular study subtopics to their broader parent course modules. Respond ONLY with valid JSON. Do not include markdown formatting or backticks, just the raw JSON object."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()["choices"][0]["message"]["content"]

with open('app/backend/scripts/katomartCourseDurations.json', 'r', encoding='utf-8') as f:
    k_data = json.load(f)

with open('app/backend/scripts/plannerData.json', 'r', encoding='utf-8') as f:
    p_data = json.load(f)

old_modules = list(k_data['subtemas'].keys())
new_db_subtemas = [st for a in p_data for m in a.get('macroThemes', []) for st in m.get('dbSubtemas', [])]

print(f"Mapping {len(new_db_subtemas)} new subtemas to {len(old_modules)} old modules...")

# Batch the subtemas to avoid token limits
mapping = {}
batch_size = 50

for i in range(0, len(new_db_subtemas), batch_size):
    batch = new_db_subtemas[i:i+batch_size]
    prompt = f"""
I have a list of broader Katomart modules:
{json.dumps(old_modules, ensure_ascii=False)}

I have a list of granular subtopics:
{json.dumps(batch, ensure_ascii=False)}

For each granular subtopic, identify the SINGLE most appropriate broader Katomart module it belongs to.
Output a JSON object where the keys are the granular subtopics and the values are the exact string of the chosen broader module.
If a subtopic combines two modules (e.g. Abdome Agudo Obstrutivo e Perfurativo), pick one of them or combine their strings exactly if they exist. Actually, just pick the most relevant one, or return null if totally unmatched.
"""
    print(f"Processing batch {i//batch_size + 1} / {len(new_db_subtemas)//batch_size + 1}...")
    try:
        response_text = call_deepseek(prompt)
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        batch_mapping = json.loads(response_text)
        mapping.update(batch_mapping)
    except Exception as e:
        print(f"Error on batch: {e}")

# Save mapping just in case
with open('app/backend/scripts/deepseek_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print("Mapping generated. Now distributing hours...")

# Count frequency of each old module
old_module_counts = {}
for new_st, old_mod in mapping.items():
    if old_mod in old_modules:
        old_module_counts[old_mod] = old_module_counts.get(old_mod, 0) + 1

new_katomart = {}
for new_st in new_db_subtemas:
    # Handle specific overrides
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
        
        # Divide hours equally among all granular subtemas that map to it
        divided_hours = round(orig_data.get("theory_hours", 1.0) / count, 2)
        
        # Minimum of 0.25h (15 mins) per subtopic just to be safe
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

print("katomartCourseDurations.json updated successfully!")
