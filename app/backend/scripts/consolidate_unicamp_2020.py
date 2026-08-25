import json
import base64
import os
import sqlite3
from collections import defaultdict
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_unicamp_multi import format_golden_explanation, infer_area_from_tags, DB_PATH, INST_CODE, INST_LABEL
from datetime import datetime, timezone
import re

har1 = r"C:\Users\wmors\Downloads\UNICAMP20201.har"
har2 = r"C:\Users\wmors\Downloads\UNICAMP_2020-2022.har"

all_2020_qs = []
seen_ids = set()

for hpath in [har1, har2]:
    with open(hpath, "r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)
    for entry in har.get("log", {}).get("entries", []):
        url = entry.get("request", {}).get("url", "")
        if "qbank/full" in url:
            resp = entry.get("response", {})
            content = resp.get("content", {})
            text = content.get("text", "")
            encoding = content.get("encoding", "")
            if text:
                if encoding == "base64":
                    text = base64.b64decode(text).decode("utf-8", errors="ignore")
                try:
                    data = json.loads(text)
                    t_name = data.get("name") or ""
                    if "2020" in t_name:
                        for q in data.get("questions", []):
                            qid = q.get("questionIdentifier") or q.get("_id")
                            if qid and qid not in seen_ids:
                                seen_ids.add(qid)
                                all_2020_qs.append((t_name, q))
                except Exception:
                    pass

print(f"Total de questões UNICAMP 2020 consolidadas: {len(all_2020_qs)}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Deletar 2020 existente
cursor.execute("SELECT id FROM questions WHERE institution_code = ? AND year = 2020", (INST_CODE,))
old_ids = [r["id"] for r in cursor.fetchall()]
if old_ids:
    placeholders = ",".join("?" * len(old_ids))
    cursor.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", old_ids)
    cursor.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", old_ids)
    cursor.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", old_ids)
    cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", old_ids)

now_iso = datetime.now(timezone.utc).isoformat()
for q_num, (tname, q) in enumerate(all_2020_qs, start=1):
    statement = (q.get("statement") or "").strip()
    golden_exp, correct_letter = format_golden_explanation(q)
    tag_objs = q.get("tags", [])
    tag_names = [t.get("name") for t in tag_objs if t.get("name")]
    topic = tag_names[0] if tag_names else "Clínica Médica Geral"
    subtema = tag_names[1] if len(tag_names) > 1 else topic
    area = infer_area_from_tags(tag_names)

    cursor.execute("""
        INSERT INTO questions (
            source_file, source_number, year, institution_code, institution_label,
            topic, stem, correct_letter, missing_alts, comment_code,
            area, subtema, editorial_status, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"{INST_CODE} 2020",
        q_num,
        2020,
        INST_CODE,
        INST_LABEL,
        topic,
        statement,
        correct_letter,
        0,
        None,
        area,
        subtema,
        "reviewed",
        "active"
    ))
    new_q_id = cursor.lastrowid

    # Alternativas
    answers = q.get("answers", [])
    if not answers:
        cursor.execute("""
            INSERT INTO alternatives (question_id, letter, text, is_correct)
            VALUES (?, 'A', 'Questão Dissertativa - Ver Padrão de Resposta no Comentário', 1)
        """, (new_q_id,))
    else:
        for aidx, a in enumerate(answers):
            let = chr(65 + aidx)
            ans_text = (a.get("answer") or "").strip()
            is_corr = 1 if a.get("rightAnswer") else 0
            cursor.execute("""
                INSERT INTO alternatives (question_id, letter, text, is_correct)
                VALUES (?, ?, ?, ?)
            """, (new_q_id, let, ans_text, is_corr))

    # Explicação
    cursor.execute("""
        INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at)
        VALUES (?, ?, ?, ?)
    """, (new_q_id, golden_exp, now_iso, now_iso))

    # Imagens
    img_urls = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', statement)
    img_tags = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', statement)
    all_imgs = list(dict.fromkeys(img_urls + img_tags))
    for order_idx, img_url in enumerate(all_imgs):
        cursor.execute("""
            INSERT INTO question_images (question_id, file_path, order_index)
            VALUES (?, ?, ?)
        """, (new_q_id, img_url, order_idx))

conn.commit()
conn.close()
print(f"[SUCESSO] UNICAMP 2020 totalmente consolidada com {len(all_2020_qs)} questões!")
