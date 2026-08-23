import json

har_path = r"C:\Users\wmors\Desktop\Ginecologia e Obstetrícia.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "20366" in url or "68001" in url or "68010" in url or "68011" in url or "85632" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        status = entry.get("response", {}).get("status", 0)
        print(f"{status} | {len(text)} bytes | {url}")
        if len(text) > 0 and len(text) < 5000:
            try:
                d = json.loads(text)
                print("  Data keys:", list(d.keys()) if isinstance(d, dict) else len(d))
                if isinstance(d, dict):
                    print("  Name/title:", d.get("name") or d.get("title"))
            except Exception:
                pass
