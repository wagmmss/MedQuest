import os
import sqlite3
import re

BACKEND_DIR = r"c:\dev\MedQuest\app\backend"
DB_PATH = os.path.join(BACKEND_DIR, "medquest.db")
STATIC_DIR = os.path.join(BACKEND_DIR, "static")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Clean question_images
print("Cleaning question_images...")
images = cur.execute("SELECT id, file_path FROM question_images").fetchall()
deleted_q_images = 0
for row in images:
    fp = row['file_path']
    full_path = os.path.join(STATIC_DIR, fp)
    if not os.path.exists(full_path):
        cur.execute("DELETE FROM question_images WHERE id = ?", (row['id'],))
        deleted_q_images += 1
print(f"Deleted {deleted_q_images} dead links from question_images.")

# 2. Clean explanations
print("Cleaning explanations...")
explanations = cur.execute("SELECT question_id, explanation_text FROM explanations").fetchall()
updated_exps = 0

def remove_dead_links(match):
    url = match.group(2)
    if '/api/images/' in url:
        rel_path = url.split('/api/images/')[-1]
        full_path = os.path.join(STATIC_DIR, rel_path)
        if not os.path.exists(full_path):
            return ""
    return match.group(0)

def remove_dead_links_html(match):
    url = match.group(1)
    if '/api/images/' in url:
        rel_path = url.split('/api/images/')[-1]
        full_path = os.path.join(STATIC_DIR, rel_path)
        if not os.path.exists(full_path):
            return ""
    return match.group(0)

for exp in explanations:
    txt = exp['explanation_text']
    if not txt: continue
    
    new_txt = re.sub(r'!\[(.*?)\]\((.*?)\)', remove_dead_links, txt)
    new_txt = re.sub(r'<img[^>]+src=["\'](.*?)["\'][^>]*>', remove_dead_links_html, new_txt)
    
    if new_txt != txt:
        cur.execute("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", (new_txt, exp['question_id']))
        updated_exps += 1

print(f"Updated {updated_exps} explanations to remove dead image links.")

# 3. Clean FTS
print("Reindexing FTS...")
cur.execute("DELETE FROM questions_fts")
cur.execute("""
    INSERT INTO questions_fts (rowid, stem, explanation)
    SELECT q.id, q.stem, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
""")

conn.commit()
conn.close()
print("Done!")
