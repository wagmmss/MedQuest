import sys
sys.path.insert(0, 'app/backend')
from api.db import get_db
from flask import Flask

app = Flask(__name__)
with app.app_context():
    print('Connecting to Turso...')
    turso_db = get_db()
    print('Querying Turso...')
    res = turso_db.execute('SELECT COUNT(*) as c FROM questions').fetchone()
    print(f'Turso questions count: {res["c"]}')
