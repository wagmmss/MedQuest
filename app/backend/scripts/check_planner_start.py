with open("app/backend/scripts/planner.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines[:60]):
    print(l, end="")
