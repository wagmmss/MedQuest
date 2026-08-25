import json
import re

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

for entry in har.get("log", {}).get("entries", []):
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            for q in data.get("questions", []):
                sku = q.get("sku", "")
                # Test regex: extract the question number part
                # SKU format: USP-SP-2026-01-R1 or USP-SP-2026-04-R1.
                m = re.search(r"\b\d{4}-(\d+)-", sku)
                qnum = int(m.group(1)) if m else None
                
                # Check alternatives
                answers = q.get("answers", [])
                right_answers = [a for a in answers if a.get("rightAnswer")]
                
                if len(answers) < 4 or len(right_answers) != 1:
                    print(f"Alts issue in SKU {sku}: {len(answers)} answers, {len(right_answers)} right answers, isDissertative={q.get('isDissertative')}, nulled={q.get('nulled')}")
                    for idx, a in enumerate(answers):
                        print(f"   Alt {idx}: right={a.get('rightAnswer')}, text={a.get('answer')}")

