import sys, os
sys.path.append('c:\\dev\\MedQuest\\app\\backend')
from app import create_app
app = create_app()
client = app.test_client()
response = client.get('/api/search?q=trauma')
print('Status:', response.status_code)
print('Data:', response.data.decode('utf-8')[:200])
