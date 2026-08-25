import json
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"

print(f"Lendo HAR: {har_path} (Tamanho: {os.path.getsize(har_path) / (1024*1024):.2f} MB)")
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total de entradas HTTP no HAR: {len(entries)}")

# Find all JSON responses
candidates = []
for i, entry in enumerate(entries):
    req = entry.get("request", {})
    url = req.get("url", "")
    method = req.get("method", "")
    
    resp = entry.get("response", {})
    status = resp.get("status", 0)
    content = resp.get("content", {})
    mime = content.get("mimeType", "")
    text = content.get("text", "")
    
    if text and ("json" in mime or text.strip().startswith(("{", "["))):
        try:
            data = json.loads(text)
            candidates.append({
                "index": i,
                "url": url,
                "method": method,
                "status": status,
                "data": data,
                "size": len(text)
            })
        except Exception:
            pass

print(f"Total de respostas JSON decodificadas: {len(candidates)}")
print("\n--- Principais endpoints encontrados ---")
for c in candidates:
    d = c["data"]
    dtype = type(d).__name__
    keys = list(d.keys())[:8] if isinstance(d, dict) else f"list of {len(d)} items"
    print(f"[{c['index']}] {c['method']} {c['url'][:90]}... -> {dtype} ({keys}) [Tamanho: {c['size']}]")

