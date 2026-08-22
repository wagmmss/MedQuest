import json
import sqlite3

def run():
    planner_json_path = r'c:\dev\MedQuest\app\backend\scripts\katomartCourseDurations.json'
    db_path = r'C:\Users\wmors\AppData\Roaming\Katomart\katomart.db'
    
    with open(planner_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    subtemas = data.get("subtemas", {})
    json_modules = set(info.get("module") for info in subtemas.values() if info.get("module"))
    print("Some modules from json:", list(json_modules)[:5])
    
    c = sqlite3.connect(db_path)
    db_modules = [r[0] for r in c.execute("SELECT title FROM modules").fetchall()]
    print("Some modules from DB:", db_modules[:5])

if __name__ == '__main__':
    run()
