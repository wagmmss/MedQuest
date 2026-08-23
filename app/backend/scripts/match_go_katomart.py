import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

with open("go_modules_raw.json", "r", encoding="utf-8") as f:
    medway_mods = json.load(f)

medway_names = [m["name"] for m in medway_mods]

print("All katomart entries matching GO keywords:")
keywords = ["mama", "parto", "gesta", "colo", "uter", "vulv", "vagin", "ovár", "ovar", "climat", "menstru", "fetal", "gravid", "puerp", "abort", "fistul", "sexual", "anticoncep", "contracep", "incontin", "prenatal", "pré-natal", "infertili", "pélv", "pelv", "endometr", "amenorr"]

for k, v in sorted(kat.get("subtemas", {}).items()):
    if any(kw in k.lower() for kw in keywords):
        print(f"  katomart: '{k}' -> {v.get('theory_hours')}h (module: {v.get('module')})")

print("\n--- 37 Medway Modules matching with Katomart ---")
for m in medway_names:
    # Look for best match
    matches = []
    for k, v in kat.get("subtemas", {}).items():
        if k.lower() == m.lower():
            matches.append((1.0, k, v))
        elif k.lower() in m.lower() or m.lower() in k.lower():
            matches.append((0.8, k, v))
        elif any(word in k.lower() for word in m.lower().split() if len(word) > 4):
            matches.append((0.5, k, v))
    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        score, k, v = matches[0]
        print(f"Medway: '{m}' ==> Katomart: '{k}' ({v.get('theory_hours')}h, score={score})")
    else:
        print(f"Medway: '{m}' ==> NO MATCH")
