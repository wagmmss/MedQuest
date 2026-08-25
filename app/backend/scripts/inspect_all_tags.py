import json
import os
import sys
from collections import Counter

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"
with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
all_questions = []
seen_ids = set()

for entry in entries:
    url = entry.get("request", {}).get("url", "")
    if "qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            for q in data.get("questions", []):
                qid = q.get("questionIdentifier") or q.get("_id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

print(f"Total questions: {len(all_questions)}")
all_tags = []
for q in all_questions:
    tags = q.get("tags", [])
    tag_names = [t.get("name") for t in tags if t.get("name")]
    all_tags.extend(tag_names)

print(f"Tags sample (Counter top 20):")
for tag, cnt in Counter(all_tags).most_common(20):
    print(f"  {tag}: {cnt}")
