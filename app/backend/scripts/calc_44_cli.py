import json

with open("clinica_extracted_themes.json", "r", encoding="utf-8") as f:
    t45 = json.load(f)

# Consolidate duplicate "Distúrbios da Hemostasia" if any
unique_cli = {}
for k, v in t45.items():
    if "Distúrbios da Hemostasia, Desordens Trombóticas" in k:
        canonical_name = "Distúrbios da Hemostasia, Desordens Trombóticas e Transfusão de Hemocomponentes"
        if canonical_name not in unique_cli:
            unique_cli[canonical_name] = v["lesson_hours"]
        else:
            unique_cli[canonical_name] += v["lesson_hours"]
    else:
        unique_cli[k] = v["lesson_hours"]

print(f"Total unique Medway Clínica Médica themes: {len(unique_cli)}")
total_cli_hours = sum(unique_cli.values())
print(f"Total theory hours for Clínica Médica: {total_cli_hours:.1f}h")
for i, (name, hours) in enumerate(sorted(unique_cli.items())):
    print(f"[{i+1:02d}] {name}: {hours:.2f}h")
