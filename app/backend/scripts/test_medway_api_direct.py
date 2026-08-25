import urllib.request
import json

url = "https://cms.medway.com.br/api/v3/questions/408817/text-explanation/?track=5992995"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://app.medway.com.br",
        "Referer": "https://app.medway.com.br/",
        "Accept": "application/json, text/plain, */*"
    }
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("RESPOSTA DA MEDWAY (Direta via API):")
        print("Keys:", list(data.keys()))
        print("Introduction:", data.get("introduction")[:150] if data.get("introduction") else "")
        print("Conclusion (Pulo do Gato):", data.get("conclusion")[:150] if data.get("conclusion") else "")
except Exception as e:
    print("Erro ao consultar:", e)
