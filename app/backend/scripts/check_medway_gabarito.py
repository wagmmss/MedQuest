import json
import base64

har_path = r"C:\Users\wmors\Downloads\MEDWAYAUTORAL.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    resp = entry.get("response", {})
    content = resp.get("content", {})
    text = content.get("text", "")
    encoding = content.get("encoding", "")
    if text and encoding == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
    if not text:
        continue
    try:
        data = json.loads(text)
        if "api/v3/questions/218253/?" in url:
            print("Question 218253:")
            print("correct_letters:", data.get("correct_letters"))
            print("options:")
            for opt in data.get("options", []):
                print(" ", opt)
        elif "api/v3/questions/218253/text-explanation" in url:
            print("\nExplanation 218253:")
            print("Keys:", list(data.keys()))
            print("actual_explanation:", data.get("actual_explanation", "")[:100])
    except Exception:
        pass
