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

print("Executing 1 update...")
resp = requests.post(url, headers=headers, json={
    'requests': [{'type': 'execute', 'stmt': {'sql': "UPDATE questions SET subtema = 'AVC isquêmico: janela de trombólise e trombectomia; AVC hemorrágico e HSA' WHERE subtema = 'AVC e Doenças Cerebrovasculares'"}}]
}, timeout=60)

print(resp.status_code)
print(resp.text)
