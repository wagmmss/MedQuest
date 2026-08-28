"""
Script para importação de provas UNICAMP do arquivo UNICAMP_2020-2025.har.
Processa questões objetivas e discursivas de 2023, 2024 e 2025,
formatando comentários no Template Ouro e indexando todas as imagens S3.
"""

import json
import os
import sys
import re
import base64
import sqlite3
from datetime import datetime, timezone
from collections import defaultdict

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

INST_CODE = "UNICAMP"
INST_LABEL = "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"

def infer_area_from_tags(tags: list[str]) -> str:
    text = " ".join(tags).lower()
    if "(cm)" in text or "clínica médica" in text or "cardiologia" in text or "pneumologia" in text or "nefrologia" in text or "neurologia" in text or "reumatologia" in text or "hematologia" in text or "infectologia" in text or "endocrinologia" in text or "gastroenterologia" in text:
        return "Clínica Médica"
    if "(cir)" in text or "cirurgia" in text or "trauma" in text or "abdome agudo" in text or "hérnia" in text or "anestesiologia" in text or "urologia" in text or "ortopedia" in text:
        return "Cirurgia"
    if "(ped)" in text or "pediatria" in text or "puericultura" in text or "neonatologia" in text:
        return "Pediatria"
    if "(go)" in text or "ginecologia" in text or "obstetrícia" in text or "parto" in text or "pré-natal" in text or "gestação" in text or "mastologia" in text:
        return "Ginecologia e Obstetrícia"
    if "(prev)" in text or "preventiva" in text or "sus" in text or "epidemiologia" in text or "saúde coletiva" in text or "bioética" in text or "estatística" in text:
        return "Medicina Preventiva"
    return "Clínica Médica"

def format_golden_explanation(q: dict) -> tuple[str, str]:
    answers = q.get("answers", [])
    correct_letters = []
    for idx, ans in enumerate(answers):
        if ans.get("rightAnswer"):
            correct_letters.append(chr(65 + idx))
            
    is_nulled = q.get("nulled", False)
    nulled_reason = q.get("nulledReason") or ""
    is_dissertative = len(answers) <= 1 or "DISCURSIVA" in q.get("sku", "")
    
    # 1. Gabarito
    if is_nulled and not correct_letters:
        correct_letter_str = "ANULADA"
        gabarito_header = f"**Gabarito**: ANULADA ({nulled_reason if nulled_reason else 'Questão anulada pela banca'})"
    elif is_dissertative:
        correct_letter_str = "A"
        gabarito_header = ""
    elif correct_letters:
        correct_letter_str = ", ".join(correct_letters) if len(correct_letters) > 1 else correct_letters[0]
        gabarito_header = f"**Gabarito**: Letra {correct_letter_str}"
        if is_nulled:
            gabarito_header += f" (ANULADA{': ' + nulled_reason if nulled_reason else ''})"
    else:
        correct_letter_str = "A"
        gabarito_header = "**Gabarito**: Letra A"
    
    # 2. Pulo do Gato (takeHomeMessage)
    thm = (q.get("takeHomeMessage") or "").strip()
    thm_clean = re.sub(r"^#+\s*Take\s*home\s*message:?\s*", "", thm, flags=re.IGNORECASE).strip()
    pulo_gato = f"**Pulo do Gato**:\n{thm_clean}" if thm_clean else "**Pulo do Gato**:\nAtenção aos achados clínicos essenciais e critérios diagnósticos do caso."

    # 3. Raciocínio Clínico (comment)
    raw_comment = (q.get("comment") or "").strip()
    clean_comment = re.sub(r"!\[video-tag-[^\]]*\]\([^\)]+\)", "", raw_comment).strip()
    clean_comment = re.sub(r"^#+\s*Coment[aá]rio:?\s*", "", clean_comment, flags=re.IGNORECASE).strip()
    raciocinio = f"**Raciocínio Clínico / Resolução Detalhada**:\n{clean_comment}" if clean_comment else ""

    # 4. Análise das Alternativas / Distratores
    if not is_dissertative:
        correct_explanations = []
        distractors_lines = []
        for idx, ans in enumerate(answers):
            let = chr(65 + idx)
            ans_comment = (ans.get("comment") or "").strip()
            ans_comment_clean = re.sub(r"<[^>]+>", " ", ans_comment).strip()
            ans_comment_clean = re.sub(r"\s+", " ", ans_comment_clean).strip()
            
            if ans.get("rightAnswer"):
                if ans_comment_clean:
                    correct_explanations.append(f"**Letra {let}**: {ans_comment_clean}" if len(correct_letters) > 1 else ans_comment_clean)
            else:
                if ans_comment_clean:
                    distractors_lines.append(f"- **Letra {let}**: {ans_comment_clean}")
                else:
                    distractors_lines.append(f"- **Letra {let}**: Incorreta.")
                    
        if correct_explanations:
            por_que_certa_text = "\n".join(correct_explanations)
        else:
            por_que_certa_text = "Alternativa correta conforme as diretrizes clínicas vigentes."

        por_que_certa = f"**Por que a Letra {correct_letter_str} é a Correta?**:\n{por_que_certa_text}"
        distratores_str = "**Análise dos Distratores**:\n" + "\n".join(distractors_lines) if distractors_lines else ""
    else:
        por_que_certa = ""
        distratores_str = ""
    
    sections = []
    if gabarito_header:
        sections.append(gabarito_header)
    sections.append(pulo_gato)
    if raciocinio:
        sections.append(raciocinio)
    if por_que_certa:
        sections.append(por_que_certa)
    if distratores_str:
        sections.append(distratores_str)
        
    return "\n\n".join(sections), correct_letter_str

def import_unicamp_multi(har_path: str):
    print(f"[HAR] Lendo arquivo: {har_path}")
    with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)

    test_map = defaultdict(list)
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
                    t_id = url.split("?")[0].split("/")[-1]
                    for q in data.get("questions", []):
                        test_map[(t_id, t_name)].append(q)
                except Exception:
                    pass

    # Group by year
    by_year = defaultdict(list)
    seen_ids = set()

    for (tid, tname), raw_qs in test_map.items():
        year_m = re.search(r"\b(202\d)\b", tname)
        if not year_m:
            continue
        year = int(year_m.group(1))

        for q in raw_qs:
            qid = q.get("questionIdentifier") or q.get("_id")
            if qid and qid not in seen_ids:
                seen_ids.add(qid)
                by_year[year].append((tname, q))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_inserted = 0
    total_images = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for year in sorted(by_year.keys(), reverse=True):
        qs_list = by_year[year]
        print(f"\n==================================================")
        print(f"[PROCESSANDO] UNICAMP {year} -> {len(qs_list)} questões extraídas")
        print(f"==================================================")

        # 1. Remover questões antigas não-autorais de UNICAMP deste ano
        cursor.execute("""
            SELECT id FROM questions
            WHERE (institution_code = ? OR institution_label = ?)
              AND year = ?
              AND COALESCE(editorial_status, '') != 'autoral'
              AND source_file NOT LIKE '%AUTORAL%'
        """, (INST_CODE, INST_LABEL, year))
        old_ids = [r["id"] for r in cursor.fetchall()]
        print(f"[BANCO] Encontradas {len(old_ids)} questões antigas não-autorais de {INST_CODE} {year}.")

        if old_ids:
            placeholders = ",".join("?" * len(old_ids))
            cursor.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", old_ids)
            print(f"[BANCO] Removidas {len(old_ids)} questões antigas.")

        # 2. Inserir novas questões
        for q_num, (tname, q) in enumerate(qs_list, start=1):
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
                f"{INST_CODE} {year}",
                q_num,
                year,
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
            total_inserted += 1

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
                total_images += 1

        print(f"[SUCESSO] Inseridas {len(qs_list)} questões oficiais para UNICAMP {year}!")

    conn.commit()
    conn.close()

    print(f"\n==================================================")
    print(f"[FINALIZADO] Total de questões UNICAMP inseridas: {total_inserted}")
    print(f"[FINALIZADO] Total de imagens indexadas: {total_images}")
    print(f"==================================================")

if __name__ == "__main__":
    har_path = r"C:\Users\wmors\Downloads\UNICAMP_2020-2025.har"
    import_unicamp_multi(har_path)
