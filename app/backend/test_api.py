import sys, os, json
sys.path.append('c:\\dev\\MedQuest\\app\\backend')
from app import create_app
app = create_app()
client = app.test_client()
response = client.get('/api/meta')
data = json.loads(response.data.decode('utf-8'))
print([i['institution_code'] for i in data.get('institutions', [])])
