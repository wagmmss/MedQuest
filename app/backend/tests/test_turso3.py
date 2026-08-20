import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
import libsql_client
from datetime import datetime, timedelta, timezone

client = libsql_client.create_client_sync(url=os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://'), auth_token=os.environ.get('TURSO_AUTH_TOKEN'))
g_user_id = '1'

def run():
    now_utc = datetime.now(timezone.utc)
    print("q1")
    client.execute("SELECT COUNT(*) n FROM questions WHERE missing_alts = 0", [])
    print("q2")
    client.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ?", [g_user_id])
    print("q3")
    client.execute("SELECT COUNT(DISTINCT question_id) n FROM attempts WHERE user_id = ?", [g_user_id])
    print("q4")
    client.execute("SELECT COUNT(*) n FROM attempts WHERE user_id = ? AND is_correct = 1", [g_user_id])
    print("q5")
    client.execute("""
        SELECT COUNT(*) n FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 1
        AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)
    """, [g_user_id, g_user_id])
    print("q6")
    client.execute("SELECT COUNT(*) n FROM spaced_repetition WHERE next_review_date <= ? AND user_id = ?", [now_utc.isoformat(), g_user_id])
    print("q7")
    client.execute("SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ? AND user_id = ?", [(now_utc - timedelta(days=7)).isoformat(), g_user_id])
    print("q8")
    client.execute("SELECT SUM(is_correct) c, COUNT(*) n FROM attempts WHERE answered_at >= ? AND answered_at < ? AND user_id = ?", [(now_utc - timedelta(days=14)).isoformat(), (now_utc - timedelta(days=7)).isoformat(), g_user_id])
    print("q9")
    client.execute("SELECT DISTINCT substr(answered_at, 1, 10) AS day FROM attempts WHERE user_id = ? ORDER BY day DESC", [g_user_id])

try:
    run()
except Exception as e:
    import traceback
    traceback.print_exc()
