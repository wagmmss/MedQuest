import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
import libsql_client
from datetime import datetime, timezone

client = libsql_client.create_client_sync(url=os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://'), auth_token=os.environ.get('TURSO_AUTH_TOKEN'))
g_user_id = '1'
now = datetime.now(timezone.utc).isoformat()

try:
    res = client.execute("""
        SELECT f.id, f.question_id, f.front, f.back, f.next_review_date, q.stem
        FROM flashcards f
        JOIN questions q ON f.question_id = q.id
        WHERE f.next_review_date <= ? AND f.user_id = ?
        ORDER BY f.next_review_date ASC LIMIT 50
    """, [now, g_user_id])
    print(res.rows)
except Exception as e:
    import traceback
    traceback.print_exc()
