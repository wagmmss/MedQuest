import json
import sqlite3
import re

def run():
    planner_json_path = r'c:\dev\MedQuest\app\backend\scripts\katomartCourseDurations.json'
    db_path = r'C:\Users\wmors\AppData\Roaming\Katomart\katomart.db'
    
    with open(planner_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    subtemas = data.get("subtemas", {})
    
    c = sqlite3.connect(db_path)
    modules_db = c.execute("SELECT id, title FROM modules").fetchall()
    
    module_durations = {}
    
    for mod_id, mod_title in modules_db:
        lessons = c.execute("SELECT title, duration FROM lessons WHERE module_id = ?", (mod_id,)).fetchall()
        
        main_lessons_duration = 0
        flash_lessons_duration = 0
        has_main_lesson = False
        
        for l_title, l_dur in lessons:
            dur = l_dur if l_dur else 0
            if "Aula Flash" in l_title:
                flash_lessons_duration += dur
            else:
                main_lessons_duration += dur
                has_main_lesson = True
                
        # The logic:
        # If there are main lessons, ignore flash lessons
        # Otherwise, keep flash lessons duration
        total_duration_sec = main_lessons_duration if has_main_lesson else flash_lessons_duration
        hours = total_duration_sec / 3600.0
        
        # Clean module title:
        # e.g. '5. Cirurgia Geral - 1. Abdome Agudo Inflamatório' -> 'Abdome Agudo Inflamatório'
        clean_title = mod_title.split(' - ')[-1].strip()
        clean_title = re.sub(r'^\d+\.\s*', '', clean_title)
        
        module_durations[clean_title] = round(hours, 2)
        
    updated_count = 0
    for subtema_nome, subtema_info in subtemas.items():
        mod_name = subtema_info.get("module")
        if mod_name and mod_name in module_durations:
            new_hours = module_durations[mod_name]
            # Some modules might have 0 duration if they have no videos.
            # In that case, keep old duration.
            if new_hours > 0:
                subtema_info["theory_hours"] = new_hours
                updated_count += 1
                
    with open(planner_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Atualizados {updated_count} subtemas com as durações calculadas de forma customizada.")

if __name__ == '__main__':
    run()
