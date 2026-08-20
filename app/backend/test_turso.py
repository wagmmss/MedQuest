import sys, os
sys.path.append('c:\\dev\\MedQuest\\app\\backend')
from api.db import get_db
from flask import Flask
app = Flask(__name__)
with app.app_context():
    db = get_db()
    print(type(db))
    res = db.execute('SELECT * FROM questions_fts WHERE questions_fts MATCH ? LIMIT 1', ('trauma',)).fetchall()
    print(res)
