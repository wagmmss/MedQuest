import sqlite3
import os

db = sqlite3.connect('medquest.db')

# Find the question
q = db.execute("SELECT id, source_file, source_number FROM questions WHERE stem LIKE '%Lactente de 2 anos%oligossintom%'").fetchall()
for row in q:
    print(f'Q ID={row[0]}, source={row[1]}, number={row[2]}')
    imgs = db.execute('SELECT file_path FROM question_images WHERE question_id = ?', (row[0],)).fetchall()
    print('  DB Images:', imgs)
    for img in imgs:
        fp = img[0]
        # Check if file exists in static/
        static_path = os.path.join('static', fp)
        print(f'    File exists at static/{fp}? {os.path.exists(static_path)}')
        # Also check frontend/public
        frontend_path = os.path.join('..', 'frontend', 'public', fp)
        print(f'    File exists at frontend/public/{fp}? {os.path.exists(frontend_path)}')

# Also check the serve_image route path
print('\n--- Checking serve_image path resolution ---')
backend_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(backend_dir, 'static')
print(f'static_dir = {static_dir}')
print(f'static_dir exists? {os.path.exists(static_dir)}')

# Check if app is using Turso (remote DB)
from dotenv import load_dotenv
load_dotenv()
turso_url = os.environ.get('TURSO_DATABASE_URL')
turso_token = os.environ.get('TURSO_AUTH_TOKEN')
print(f'\nTURSO_DATABASE_URL = {turso_url}')
print(f'TURSO_AUTH_TOKEN = {"set" if turso_token else "not set"}')
