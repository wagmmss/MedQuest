import urllib.request
import json

for port in [5000, 5001, 8000, 3000, 5173]:
    try:
        url = f"http://127.0.0.1:{port}/api/questions/meta"
        req = urllib.request.Request(url, headers={"X-User-ID": "dev-user"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Backend respondendo na porta {port}!")
            print(f"  Total no endpoint /meta: {data.get('total')}")
            for inst in data.get("institutions", [])[:5]:
                print(f"    {inst.get('institution_code')}: {inst.get('n')}")
    except Exception as e:
        pass
