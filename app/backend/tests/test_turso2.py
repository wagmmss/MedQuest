import os
import sys

sys.path.insert(0, '.')
from dotenv import load_dotenv

load_dotenv()
import libsql_client

client = libsql_client.create_client_sync(url=os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://'), auth_token=os.environ.get('TURSO_AUTH_TOKEN'))
try:
    print(client.execute('SELECT COUNT(*) n FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 1 AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)', ['1', '1']).rows)
except Exception:
    import traceback
    traceback.print_exc()
