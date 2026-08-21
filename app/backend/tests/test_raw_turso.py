import os

import requests
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get('TURSO_DATABASE_URL').replace('libsql://', 'https://')
token = os.environ.get('TURSO_AUTH_TOKEN')

# Turso HRANA / HTTP v2 protocol expects:
# POST /v2/pipeline
payload = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": "SELECT f.id, f.question_id, f.front, f.back, f.next_review_date, q.stem FROM flashcards f JOIN questions q ON f.question_id = q.id WHERE f.next_review_date <= ? AND f.user_id = ? ORDER BY f.next_review_date ASC LIMIT 50",
                "args": [{"type": "text", "value": "2026-08-08T00:00:00"}, {"type": "text", "value": "1"}]
            }
        }
    ]
}

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
r = requests.post(f"{url}/v2/pipeline", json=payload, headers=headers)
print("Status:", r.status_code)
print("Response:", r.text)
