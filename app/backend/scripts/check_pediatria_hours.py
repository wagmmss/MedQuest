import json

with open("app/backend/scripts/katomartCourseDurations.json", "r", encoding="utf-8") as f:
    kat = json.load(f)

with open("pediatria_modules_raw.json", "r", encoding="utf-8") as f:
    modules = json.load(f)

print("Katomart match for Pediatria modules:")
for m in modules:
    name = m["name"]
    # match
    k_match = kat.get("subtemas", {}).get(name)
    if not k_match:
        for k, v in kat.get("subtemas", {}).items():
            if k.lower() == name.lower() or name.lower() in k.lower() or k.lower() in name.lower():
                k_match = v
                break
    dur = k_match.get("theory_hours") if k_match else None
    mod = k_match.get("module") if k_match else None
    print(f" - '{name}' => {dur}h (Katomart: {mod})")
