import os
import sqlite3
import re

db_path = r'C:\dev\MedQuest\app\backend\medquest.db'
review_dir = r'C:\dev\MedQuest\app\backend\static\images\review'
static_dir = r'C:\dev\MedQuest\app\backend\static'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Missing in review (question_images)
images = cur.execute("SELECT id, question_id, file_path, order_index FROM question_images").fetchall()

missing_in_review = []
for row in images:
    q_id = row['question_id']
    order = row['order_index']
    
    found = False
    for ext in ['.png', '.jpg', '.gif', '.webp']:
        filename = f'q{q_id}_idx{order}{ext}'
        if os.path.exists(os.path.join(review_dir, filename)):
            found = True
            break
            
    if not found:
        missing_in_review.append(row)
        # DELETE from database
        cur.execute("DELETE FROM question_images WHERE id = ?", (row['id'],))

print(f'Deleted {len(missing_in_review)} rows from question_images.')
for m in missing_in_review:
    print(f"  -> QID: {m['question_id']}, order: {m['order_index']}")

# 2. Missing in static/images (explanations)
explanations = cur.execute("SELECT question_id, explanation_text FROM explanations").fetchall()
updated_exps = 0

def remove_dead_links(match):
    url = match.group(2)
    if '/api/images/' in url:
        rel_path = url.split('/api/images/')[-1]
        full_path = os.path.join(static_dir, rel_path.replace('/', os.sep))
        if not os.path.exists(full_path):
            print(f"  -> Removed dead link from explanation QID: {exp['question_id']}")
            return ""
    return match.group(0)

def remove_dead_links_html(match):
    url = match.group(1)
    if '/api/images/' in url:
        rel_path = url.split('/api/images/')[-1]
        full_path = os.path.join(static_dir, rel_path.replace('/', os.sep))
        if not os.path.exists(full_path):
            print(f"  -> Removed dead link from explanation QID: {exp['question_id']}")
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

# Rebuild FTS
print("Rebuilding FTS...")
cur.execute("DELETE FROM questions_fts")
cur.execute("""
    INSERT INTO questions_fts (rowid, stem, explanation)
    SELECT q.id, q.stem, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
""")

conn.commit()
conn.close()
