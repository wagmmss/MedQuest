import os
import requests
from dotenv import load_dotenv

load_dotenv('app/backend/.env')
url = os.environ['TURSO_DATABASE_URL'].replace('libsql://', 'https://') + '/v2/pipeline'
token = os.environ['TURSO_AUTH_TOKEN']

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

resp = requests.post(url, headers=headers, json={
    'requests': [{'type': 'execute', 'stmt': {'sql': "EXPLAIN QUERY PLAN UPDATE questions SET subtema = 'TEST' WHERE id = 1"}}]
})
print(resp.text)
