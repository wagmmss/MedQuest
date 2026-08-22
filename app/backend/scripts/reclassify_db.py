import sqlite3
import json
import re
import os
import sys
from openai import OpenAI
import time

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

# 1. Parse plannerData.ts to get the granular topics (details) for each area
TS_FILE = r'C:\dev\MedQuest\app\frontend\src\lib\plannerData.ts'
with open(TS_FILE, 'r', encoding='utf-8') as f:
    ts_content = f.read()

# We need a robust regex to find areas and their details
# Since TS is nested, let's extract block by block
areas_map = {} # area -> list of details strings
current_area = None

for line in ts_content.split('\n'):
    area_match = re.search(r'"area":\s*"([^"]+)"', line)
    if area_match:
        current_area = area_match.group(1)
        if current_area not in areas_map:
            areas_map[current_area] = []
    
    # Actually, extracting details using line-by-line is hard because details: [ "a", "b" ] can span multiple lines.
    
# Let's use a better regex on the full string
# Split by '"area":'
areas_splits = ts_content.split('"area":')
for split in areas_splits[1:]:
    area_name = re.search(r'\s*"([^"]+)"', split)
    if not area_name:
        continue
    area = area_name.group(1)
    areas_map[area] = []
    
    # find all "details": [ ... ]
    details_blocks = re.findall(r'"details":\s*\[(.*?)\]', split, flags=re.DOTALL)
    for block in details_blocks:
        # extract strings
        strings = re.findall(r'"([^"]+)"', block)
        areas_map[area].extend(strings)

for area, details in areas_map.items():
    print(f"Area {area}: {len(details)} details")

# Connect to DB
DB_FILE = r'C:\dev\MedQuest\app\backend\medquest.db'
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Get all questions
cursor.execute("SELECT id, area, stem, correct_letter FROM questions WHERE status='active' AND stem IS NOT NULL AND area = 'Medicina Preventiva e Social'")
questions = cursor.fetchall()

print(f"Total questions to process: {len(questions)}")

# Group questions by area
qs_by_area = {}
for q in questions:
    qid, area, stem, correct = q
    if area not in qs_by_area:
        qs_by_area[area] = []
    qs_by_area[area].append((qid, stem, correct))

total_processed = 0

for area, qs in qs_by_area.items():
    details_list = areas_map.get(area, [])
    if area == "Medicina Preventiva e Social" and not details_list:
        details_list = areas_map.get("Medicina Preventiva", [])
        
    if not details_list:
        print(f"Skipping area {area} because no details found in plannerData.ts")
        continue
    
    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(qs), batch_size):
        batch = qs[i:i+batch_size]
        
        prompt = f"Você é um especialista médico. Classifique as seguintes {len(batch)} questões da área '{area}' em EXATAMENTE UM dos tópicos abaixo.\n\n"
        prompt += "TÓPICOS DISPONÍVEIS:\n"
        for idx, t in enumerate(details_list):
            prompt += f"{idx}. {t}\n"
            
        prompt += "\nQUESTÕES PARA CLASSIFICAR:\n"
        for qid, stem, correct in batch:
            stem_trunc = stem[:600] + ("..." if len(stem) > 600 else "")
            prompt += f"--- Questão ID {qid} ---\n{stem_trunc}\n"
            
        prompt += "\nRetorne APENAS um JSON estrito no seguinte formato, e absolutamente mais nada:\n"
        prompt += '{"results": [{"id": <ID_DA_QUESTAO>, "topic_index": <INDEX_DO_TOPICO>}, ...]}'
        
        # Call DeepSeek API
        try:
            print(f"Processing batch of {len(batch)} questions for {area}...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful medical classification assistant that outputs only raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            # Clean potential markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            res_json = json.loads(content)
            
            # Update DB
            for item in res_json.get("results", []):
                q_id = item["id"]
                topic_idx = item["topic_index"]
                if 0 <= topic_idx < len(details_list):
                    chosen_topic = details_list[topic_idx]
                    cursor.execute("UPDATE questions SET subtema = ? WHERE id = ?", (chosen_topic, q_id))
            
            conn.commit()
            total_processed += len(batch)
            print(f"Success! Processed {total_processed} questions total.")
            
        except Exception as e:
            print(f"Error processing batch: {e}")
            time.sleep(2) # wait a bit before retrying or continuing
            
print("Done!")
conn.close()
