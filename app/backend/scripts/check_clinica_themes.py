import json

with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    themes = json.load(f)

print(f"Total themes in clinica_extracted_themes.json: {len(themes)}")
if isinstance(themes, list):
    for i, t in enumerate(themes):
        name = t.get("name") or t.get("title")
        print(f"[{i+1:02d}] {name} -> {t.get('lesson_hours')}h")
