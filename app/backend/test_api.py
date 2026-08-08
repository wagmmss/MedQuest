import urllib.request
import json

data = json.dumps({"selected_letter": "A", "time_spent_ms": 1000, "confidence": "certeza"}).encode('utf-8')
req = urllib.request.Request('http://localhost:5050/api/questions/1/attempt', data=data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Exception:", str(e))
