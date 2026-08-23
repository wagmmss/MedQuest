import json

with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    t45 = json.load(f)

print("Type of t45:", type(t45))
if isinstance(t45, list):
    for i, item in enumerate(t45):
        print(f"[{i+1:02d}] {item}")
elif isinstance(t45, dict):
    for i, (k, v) in enumerate(t45.items()):
        print(f"[{i+1:02d}] {k} -> {v}")
