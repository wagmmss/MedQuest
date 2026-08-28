"""
Script para importação e organização de todos os simulados autorais do arquivo VARIASBANCASAUTORAL_2026.har.
Insere todos os lotes com editorial_status = 'autoral', Template Ouro completo e indexação de imagens S3,
sem alterar nenhuma prova oficial do banco de dados.
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

INSTITUTIONS = {
    "USP-SP": ("USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"),
    "USP-RP": ("USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"),
    "UNIFESP": ("UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"),
    "UNICAMP": ("UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"),
    "SCM-SP": ("SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"),
    "SCMSP": ("SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"),
    "HSL": ("HSL", "Hospital Sírio-Libanês (HSL)"),
    "EINSTEIN": ("EINSTEIN", "Hospital Israelita Albert Einstein (HIAE)"),
    "HIAE": ("EINSTEIN", "Hospital Israelita Albert Einstein (HIAE)")
}

def detect_inst_from_name(tname: str):
    tup = tname.upper()
    if "USP-SP" in tup or "FMUSP" in tup:
        return INSTITUTIONS["USP-SP"]
    if "USP-RP" in tup or "HCRP" in tup:
        return INSTITUTIONS["USP-RP"]
    if "UNIFESP" in tup:
        return INSTITUTIONS["UNIFESP"]
    if "UNICAMP" in tup:
        return INSTITUTIONS["UNICAMP"]
    if "SCM" in tup or "SANTA" in tup:
        return INSTITUTIONS["SCMSP"]
    if "HSL" in tup or "SIRIO" in tup or "SÍRIO" in tup:
        return INSTITUTIONS["HSL"]
    if "EINSTEIN" in tup or "HIAE" in tup:
        return INSTITUTIONS["EINSTEIN"]
    return ("USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)")

def infer_area_from_tags(tags: list[str], tname: str = "") -> str:
    combined = (" ".join(tags) + " " + tname).lower()
    if "cir" in combined or "cirurgia" in combined or "trauma" in combined or "abdome agudo" in combined or "hérnia" in combined or "urologia" in combined:
        return "Cirurgia"
    if "ped" in combined or "pediatria" in combined or "puericultura" in combined or "neonatologia" in combined:
        return "Pediatria"
    if "go" in combined or "ginecologia" in combined or "obstetrícia" in combined or "fetal" in combined or "parto" in combined or "gestação" in combined:
        return "Ginecologia e Obstetrícia"
    if "prev" in combined or "preventiva" in combined or "sus" in combined or "epidemiologia" in combined or "saúde coletiva" in combined:
        return "Medicina Preventiva"
    if "cm" in combined or "clínica médica" in combined or "cardiologia" in combined or "pneumologia" in combined or "nefrologia" in combined:
        return "Clínica Médica"
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

def import_varias_autorais(har_path: str):
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

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_inserted = 0
    total_images = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for (tid, tname), raw_qs in sorted(test_map.items(), key=lambda x: x[0][1]):
        # Limpar nome do teste para o source_file
        # Ex: "EINSTEIN 2026 AUTORAL 25/08/2026, 09:32" -> "EINSTEIN 2026 AUTORAL"
        clean_name = re.sub(r"\s+\d\d/\d\d/\d\d\d\d,.*$", "", tname).strip()
        inst_code, inst_label = detect_inst_from_name(clean_name)
        year = 2026

        seen = set()
        uniq_qs = []
        for q in raw_qs:
            qid = q.get("questionIdentifier") or q.get("_id")
            if qid not in seen:
                seen.add(qid)
                uniq_qs.append(q)

        print(f"\n==================================================")
        print(f"[PROCESSANDO] {clean_name} -> {inst_code} ({len(uniq_qs)} questões)")
        print(f"==================================================")

        # 1. Remover APENAS lote autoral anterior com esse mesmo source_file
        cursor.execute("""
            SELECT id FROM questions
            WHERE source_file = ? AND editorial_status = 'autoral'
        """, (clean_name,))
        old_ids = [r["id"] for r in cursor.fetchall()]
        if old_ids:
            placeholders = ",".join("?" * len(old_ids))
            cursor.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", old_ids)
            cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", old_ids)
            print(f"[BANCO] Removidas {len(old_ids)} questões autorais antigas de {clean_name}.")

        # 2. Inserir novas questões autorais
        for q_num, q in enumerate(uniq_qs, start=1):
            statement = (q.get("statement") or "").strip()
            golden_exp, correct_letter = format_golden_explanation(q)

            tag_objs = q.get("tags", [])
            tag_names = [t.get("name") for t in tag_objs if t.get("name")]
            topic = tag_names[0] if tag_names else "Clínica Médica Geral"
            subtema = tag_names[1] if len(tag_names) > 1 else topic
            area = infer_area_from_tags(tag_names, clean_name)

            cursor.execute("""
                INSERT INTO questions (
                    source_file, source_number, year, institution_code, institution_label,
                    topic, stem, correct_letter, missing_alts, comment_code,
                    area, subtema, editorial_status, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_name,
                q_num,
                year,
                inst_code,
                inst_label,
                topic,
                statement,
                correct_letter,
                0,
                None,
                area,
                subtema,
                "autoral",
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

        print(f"[SUCESSO] Inseridas {len(uniq_qs)} questões autorais para {clean_name}!")

    conn.commit()
    conn.close()

    print(f"\n==================================================")
    print(f"[FINALIZADO] Total de questões autorais inseridas: {total_inserted}")
    print(f"[FINALIZADO] Total de imagens indexadas: {total_images}")
    print(f"==================================================")

if __name__ == "__main__":
    har_path = r"C:\Users\wmors\Downloads\VARIASBANCASAUTORAL_2026.har"
    import_varias_autorais(har_path)
