import json
import base64
from collections import defaultdict

har1_path = r"C:\Users\wmors\Downloads\UNICAMP20201.har"
har2_path = r"C:\Users\wmors\Downloads\UNICAMP20202.har"

def analyze_har(har_path, label):
    print("=" * 70)
    print(f" ANÁLISE DETALHADA: {label} ({har_path})")
    print("=" * 70)
    
    with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    print(f"Total de requisições HTTP: {len(entries)}")

    api_endpoints = []
    questions = []
    seen_ids = set()
    pagination_info = []

    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        if "qbank-api.medcof.tech" in url or "qbank/full" in url:
            api_endpoints.append(url)
            resp = entry.get("response", {})
            content = resp.get("content", {})
            text = content.get("text", "")
            encoding = content.get("encoding", "")
            if text:
                if encoding == "base64":
                    text = base64.b64decode(text).decode("utf-8", errors="ignore")
                try:
                    data = json.loads(text)
                    pag = data.get("pagination")
                    if pag:
                        pagination_info.append((url, pag))
                    for q in data.get("questions", []):
                        qid = q.get("questionIdentifier") or q.get("_id")
                        if qid and qid not in seen_ids:
                            seen_ids.add(qid)
                            questions.append(q)
                except Exception as e:
                    pass

    print(f"Requisições à API QBank: {len(api_endpoints)}")
    for ep in set(api_endpoints):
        print(f"  - Endpoint: {ep}")

    print(f"\nPaginações capturadas: {len(pagination_info)}")
    for url, pag in pagination_info:
        print(f"  - Page {pag.get('page')}/{pag.get('totalPages')} (Total elements: {pag.get('totalElements')}) -> {url.split('?')[0]}")

    print(f"\nTotal de questões únicas capturadas: {len(questions)}")

    # Quality metrics
    with_statement = sum(1 for q in questions if q.get("statement"))
    with_answers = sum(1 for q in questions if len(q.get("answers", [])) > 0)
    with_correct_ans = sum(1 for q in questions if any(a.get("rightAnswer") for a in q.get("answers", [])))
    with_comment = sum(1 for q in questions if q.get("comment"))
    with_thm = sum(1 for q in questions if q.get("takeHomeMessage"))
    
    # Image count
    total_imgs = 0
    for q in questions:
        st = q.get("statement") or ""
        total_imgs += len(re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', st))
        total_imgs += len(re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', st))

    print(f"Métricas de Conteúdo:")
    print(f"  - Questões com Enunciado: {with_statement} / {len(questions)}")
    print(f"  - Questões com Alternativas: {with_answers} / {len(questions)}")
    print(f"  - Questões com Gabarito (rightAnswer): {with_correct_ans} / {len(questions)}")
    print(f"  - Questões com Comentário Clínico: {with_comment} / {len(questions)}")
    print(f"  - Questões com Pulo do Gato (takeHomeMessage): {with_thm} / {len(questions)}")
    print(f"  - Total de Imagens encontradas nos enunciados: {total_imgs}")

    return {
        "entries": len(entries),
        "api_calls": len(api_endpoints),
        "questions_count": len(questions),
        "questions_ids": seen_ids,
        "with_comment": with_comment,
        "with_thm": with_thm,
        "total_imgs": total_imgs,
        "questions": questions
    }

import re
res1 = analyze_har(har1_path, "UNICAMP20201.har (Sem transitar)")
print("\n")
res2 = analyze_har(har2_path, "UNICAMP20202.har (Transitando por todas)")

print("\n" + "=" * 70)
print(" COMPARATIVO DIRETO: HAR 1 vs HAR 2")
print("=" * 70)
print(f"Tamanho do arquivo:  HAR 1 = 1.3 MB  |  HAR 2 = 7.1 MB")
print(f"Total de questões:   HAR 1 = {res1['questions_count']}  |  HAR 2 = {res2['questions_count']}")
print(f"Comentários:         HAR 1 = {res1['with_comment']}  |  HAR 2 = {res2['with_comment']}")
print(f"Pulo do Gato:        HAR 1 = {res1['with_thm']}  |  HAR 2 = {res2['with_thm']}")
print(f"Imagens no texto:    HAR 1 = {res1['total_imgs']}  |  HAR 2 = {res2['total_imgs']}")

missing_in_1 = res2['questions_ids'] - res1['questions_ids']
print(f"\nQuestões que faltaram no HAR 1 (mas vieram no HAR 2): {len(missing_in_1)}")
if missing_in_1:
    missing_nums = []
    for q in res2['questions']:
        qid = q.get("questionIdentifier") or q.get("_id")
        if qid in missing_in_1:
            missing_nums.append(q.get("sku") or qid)
    print(f"Amostra das questões faltantes no HAR 1: {missing_nums[:5]}...")
