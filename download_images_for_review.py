import os
import sqlite3
import urllib.request
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

BACKEND_DIR = r"c:\dev\MedQuest\app\backend"
DB_PATH = os.path.join(BACKEND_DIR, "medquest.db")
REVIEW_DIR = os.path.join(BACKEND_DIR, "static", "images", "review")

os.makedirs(REVIEW_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

images = cur.execute("SELECT question_id, file_path, order_index FROM question_images").fetchall()

# Also get from explanations? The user said "essas 1321 imagens". But let's check explanations just in case.
# If I need explanations too, I'd have to parse them. For now let's focus on question_images as they are 1321.

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def download_image(q_id, url, order_index):
    if not url.startswith('http'):
        return None
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
            # Guess extension
            ext = ".png"
            if data.startswith(b'\xff\xd8\xff'): ext = ".jpg"
            elif data.startswith(b'GIF'): ext = ".gif"
            elif data.startswith(b'RIFF') and b'WEBP' in data[:16]: ext = ".webp"
            
            filename = f"q{q_id}_idx{order_index}{ext}"
            filepath = os.path.join(REVIEW_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(data)
            return filepath
    except Exception as e:
        return str(e)

tasks = []
for row in images:
    tasks.append((row['question_id'], row['file_path'], row['order_index']))

print(f"Downloading {len(tasks)} images for review...")
success = 0
errors = 0

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(download_image, t[0], t[1], t[2]) for t in tasks]
    for future in as_completed(futures):
        res = future.result()
        if res and not res.startswith("http") and not "Error" in res:
            success += 1
        elif res:
            errors += 1

print(f"Downloaded {success} images. Errors: {errors}")
