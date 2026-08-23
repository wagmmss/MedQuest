import json

with open('medway_modules.json', 'r', encoding='utf-8') as f:
    mods = json.load(f)

print(f"Total modules in GO: {len(mods)}")
total_lessons = 0
for m in mods:
    lessons = [item for item in m.get('module_items', []) if item.get('content_type') == 'lesson']
    total_lessons += len(lessons)
    print(f"{m['order']}. {m['name']} -> {len(lessons)} lessons ({len(m.get('module_items', []))} total items)")

print(f"Total video lessons in GO alone: {total_lessons}")
