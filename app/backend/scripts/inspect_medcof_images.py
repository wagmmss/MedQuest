import json
import re

har_path = r"C:\Users\wmors\Downloads\USP_SP_2026.har"

with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
    har = json.load(f)

entries = har.get("log", {}).get("entries", [])
all_questions = []
seen_ids = set()

for entry in entries:
    url = entry.get("request", {}).get("url", "")
    if "qbank-api.medcof.tech/v3/qbank/full" in url:
        text = entry.get("response", {}).get("content", {}).get("text", "")
        if text:
            data = json.loads(text)
            for q in data.get("questions", []):
                qid = q.get("questionIdentifier") or q.get("_id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)

questions_with_images = []
for q in all_questions:
    statement = q.get("statement", "")
    sku = q.get("sku", "")
    # Check for markdown images or img tags
    img_urls = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', statement)
    img_tags = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', statement)
    all_imgs = img_urls + img_tags
    if all_imgs:
        questions_with_images.append((sku, all_imgs))

print(f"Total questoes com imagens no enunciado: {len(questions_with_images)}")
for sku, imgs in questions_with_images[:10]:
    print(f"  {sku}: {len(imgs)} imagem(ns) -> {imgs[0]}")
