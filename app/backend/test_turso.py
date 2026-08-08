import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from api.db import get_db
import libsql_client

client = libsql_client.create_client_sync(url=os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://'), auth_token=os.environ.get('TURSO_AUTH_TOKEN'))
try:
    print(client.execute('SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ? AND user_id = ?', ['2026-08-08T00:00:00', '1']).rows)
except Exception as e:
    import traceback
    traceback.print_exc()
