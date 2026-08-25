import json
import base64

har_path = r"C:\Users\wmors\Downloads\USP_SP_2024.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
print(f"Total entries: {len(entries)}")

for i, entry in enumerate(entries):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        resp = entry.get("response", {})
        status = resp.get("status")
        content = resp.get("content", {})
        mime = content.get("mimeType", "")
        text = content.get("text", "")
        encoding = content.get("encoding", "")
        size = content.get("size", 0)
        
        print(f"\nEntry [{i}] -> URL: {url}")
        print(f"  Status: {status}, Mime: {mime}, Encoding: {encoding}, Size: {size}, TextLen: {len(text) if text else 0}")
        if text:
            print(f"  Text preview (first 100): {text[:100]!r}")
            if encoding == "base64":
                try:
                    decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
                    print(f"  Base64 decoded preview: {decoded[:100]!r}")
                except Exception as e:
                    print("  Base64 decode error:", e)

