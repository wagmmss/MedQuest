import json
import sys

sys.path.append('c:\\dev\\MedQuest\\app\\backend')
from app import create_app

app = create_app()
client = app.test_client()
response = client.get('/api/meta')
print(response.status_code)
data = json.loads(response.data.decode('utf-8'))
print(len(data.get('institutions', [])))
