import os
from dotenv import load_dotenv
import sqlite3
import libsql

load_dotenv('app/backend/.env')

print("Connecting to Turso...")
turso_conn = libsql.connect(
    os.environ['TURSO_DATABASE_URL'], 
    auth_token=os.environ['TURSO_AUTH_TOKEN']
)

print("Fixing AVC...")
turso_conn.execute("UPDATE questions SET subtema = 'AVC isquêmico: janela de trombólise e trombectomia; AVC hemorrágico e HSA' WHERE subtema = 'AVC e Doenças Cerebrovasculares'")
turso_conn.commit()

print("Checking what else was changed by the old script...")
remote_rows = turso_conn.execute("SELECT DISTINCT subtema FROM questions WHERE area = 'Cirurgia'").fetchall()
print([r[0] for r in remote_rows])
