import os
import sys

sys.path.insert(0, '.')
from dotenv import load_dotenv

load_dotenv()
import libsql_client

client = libsql_client.create_client_sync(url=os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://'), auth_token=os.environ.get('TURSO_AUTH_TOKEN'))

try:
    res = client.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", [r[0] for r in res.rows])
except Exception:
    import traceback
    traceback.print_exc()
