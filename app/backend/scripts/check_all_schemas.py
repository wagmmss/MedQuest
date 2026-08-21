import json
import sqlite3

conn = sqlite3.connect('medquest.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
schema = {}
for (table,) in tables:
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    schema[table] = columns
print(json.dumps(schema, indent=2))
