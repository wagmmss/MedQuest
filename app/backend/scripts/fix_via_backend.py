from api.db import get_db, db_transaction
from flask import Flask

app = Flask(__name__)
app.config['TESTING'] = True

with app.app_context():
    db = get_db()
    
    # 1. Check current state
    if hasattr(db, "batch"):
        res = db.batch([("SELECT DISTINCT subtema FROM questions WHERE subtema LIKE '%AVC%'", ())])
        print("Before:", res[0].fetchall())
    else:
        print("Before:", db.execute("SELECT DISTINCT subtema FROM questions WHERE subtema LIKE '%AVC%'").fetchall())

    # 2. Update
    with db_transaction(db, immediate=True):
        db.execute("UPDATE questions SET subtema = 'AVC isquêmico: janela de trombólise e trombectomia; AVC hemorrágico e HSA' WHERE subtema = 'AVC e Doenças Cerebrovasculares'")
        # Também atualizamos qualquer outro que esteja quebrado, como Abdome Agudo Obstrutivo -> Abdome Agudo Obstrutivo e Perfurativo
        db.execute("UPDATE questions SET subtema = 'Abdome Agudo Obstrutivo e Perfurativo' WHERE subtema = 'Abdome Agudo Obstrutivo'")

    # 3. Verify
    if hasattr(db, "batch"):
        res = db.batch([("SELECT DISTINCT subtema FROM questions WHERE subtema LIKE '%AVC%'", ())])
        print("After:", res[0].fetchall())
    else:
        print("After:", db.execute("SELECT DISTINCT subtema FROM questions WHERE subtema LIKE '%AVC%'").fetchall())

    print("Success!")
