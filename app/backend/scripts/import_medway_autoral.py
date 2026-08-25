"""
Script universal para importação de qualquer simulado autoral da Medway (Objetivas e Discursivas).
Processa os dados de HAR, converte para o Template Ouro (5 Pilares),
associa imagens e insere com editorial_status = 'autoral' no medquest.db.
"""

import json
import os
import sys
import re
import html
import base64
import sqlite3
from datetime import datetime, timezone

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

INSTITUTIONS = {
    "USP-SP": ("USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"),
    "USP-RP": ("USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"),
    "UNIFESP": ("UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"),
    "UNICAMP": ("UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"),
    "SCMSP": ("SCMSP", "Santa Casa de Misericórdia de São Paulo (SCMSP)"),
    "HSL": ("HSL", "Hospital Sírio-Libanês (HSL)"),
    "EINSTEIN": ("EINSTEIN", "Hospital Israelita Albert Einstein (HIAE)")
}

def detect_inst_from_title(title: str):
    t = title.upper()
    if "USP-SP" in t or "FMUSP" in t:
        return INSTITUTIONS["USP-SP"]
    if "USP-RP" in t or "HCRP" in t:
        return INSTITUTIONS["USP-RP"]
    if "UNICAMP" in t:
        return INSTITUTIONS["UNICAMP"]
    if "UNIFESP" in t:
        return INSTITUTIONS["UNIFESP"]
    if "SCM" in t or "SANTA" in t:
        return INSTITUTIONS["SCMSP"]
    if "HSL" in t or "SÍRIO" in t or "SIRIO" in t:
        return INSTITUTIONS["HSL"]
    if "EINSTEIN" in t or "HIAE" in t:
        return INSTITUTIONS["EINSTEIN"]
    return ("USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)")

def clean_html_to_markdown(raw_html: str) -> str:
    if not raw_html:
        return ""
    txt = html.unescape(raw_html)
    txt = re.sub(r'</p>\s*<p[^>]*>', '\n\n', txt)
    txt = re.sub(r'<br\s*/?>', '\n', txt)
    txt = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', txt, flags=re.DOTALL)
    txt = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', txt, flags=re.DOTALL)
    txt = re.sub(r'<img[^>]+src=["\'](https?://[^"\']+)["\'][^>]*>', r'![imagem](\1)', txt)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = re.sub(r'[ \t]+', ' ', txt)
    txt = re.sub(r'\n\s*\n\s*\n+', '\n\n', txt)
    return txt.strip()

def infer_area_from_tags(speciality: str, tags: list[str]) -> str:
    combined = (speciality + " " + " ".join(tags)).lower()
    if "cir" in combined or "cirurgia" in combined or "trauma" in combined or "abdome agudo" in combined or "urologia" in combined:
        return "Cirurgia"
    if "ped" in combined or "pediatria" in combined or "puericultura" in combined or "neonatologia" in combined:
        return "Pediatria"
    if "go" in combined or "ginecologia" in combined or "obstetrícia" in combined or "fetal" in combined or "parto" in combined or "gestação" in combined:
        return "Ginecologia e Obstetrícia"
    if "prev" in combined or "preventiva" in combined or "sus" in combined or "epidemiologia" in combined or "saúde coletiva" in combined or "trabalhador" in combined:
        return "Medicina Preventiva"
    if "cm" in combined or "clínica médica" in combined or "cardiologia" in combined or "pneumologia" in combined or "nefrologia" in combined:
        return "Clínica Médica"
    return "Clínica Médica"

def extract_gabarito(exp_dict, options_list):
    if not exp_dict or not options_list:
        return "A"
        
    scores = {}
    for opt in options_list:
        let = opt.get("letter", "").lower()
        raw_opt = exp_dict.get(f"option_{let}", "") or ""
        raw_short = exp_dict.get(f"short_option_{let}", "") or ""
        txt = html.unescape(raw_opt + " " + raw_short)
        txt_clean = re.sub(r"<[^>]+>", " ", txt).strip().lower()
        
        is_correct = False
        is_incorrect = False
        
        if "incorret" in txt_clean[:40] or "errad" in txt_clean[:40] or "distrator" in txt_clean[:40]:
            is_incorrect = True
        if "corret" in txt_clean[:40] or "certa" in txt_clean[:40] or "gabarito" in txt_clean[:40] or "resposta certa" in txt_clean or "resposta correta" in txt_clean or "esta é a resposta correta" in txt_clean:
            is_correct = True
            
        if is_correct and not is_incorrect:
            scores[let.upper()] = 10
        elif is_incorrect:
            scores[let.upper()] = -10
        else:
            scores[let.upper()] = 0
            
    if scores:
        best_let = max(scores.items(), key=lambda x: x[1])[0]
        return best_let
    return "A"

def format_medway_golden_explanation(exp_dict: dict, options_list: list, correct_letter: str, is_discursive: bool = False) -> str:
    # 1. Gabarito
    if is_discursive or not options_list:
        gabarito_header = "**Gabarito**: DISCURSIVA / RESPOSTA CURTA (Ver Padrão de Resposta abaixo)"
    else:
        gabarito_header = f"**Gabarito**: Letra {correct_letter}"
    
    # 2. Pulo do Gato (conclusion)
    conclusion_raw = exp_dict.get("conclusion") or ""
    conclusion_clean = clean_html_to_markdown(conclusion_raw)
    pulo_gato = f"**Pulo do Gato**:\n{conclusion_clean}" if conclusion_clean else "**Pulo do Gato**:\nAtenção aos conceitos centrais e critérios diagnósticos explorados pela banca."

    # 3. Raciocínio Clínico (introduction / actual_explanation)
    intro_raw = exp_dict.get("introduction") or exp_dict.get("actual_explanation") or exp_dict.get("full_explanation") or ""
    intro_clean = clean_html_to_markdown(intro_raw)
    header_raciocinio = "**Raciocínio Clínico / Padrão de Resposta Esperado**:" if (is_discursive or not options_list) else "**Raciocínio Clínico**:"
    raciocinio = f"{header_raciocinio}\n{intro_clean}" if intro_clean else ""

    # 4. Análise das Alternativas e Distratores (apenas objetivas)
    if not is_discursive and options_list:
        correct_text = ""
        distractors_lines = []
        for opt in options_list:
            let = opt.get("letter", "").upper()
            let_lower = let.lower()
            opt_raw = exp_dict.get(f"option_{let_lower}") or exp_dict.get(f"short_option_{let_lower}") or ""
            opt_clean = clean_html_to_markdown(opt_raw)
            opt_clean_body = re.sub(r"^[A-E]\)\s*", "", opt_clean, flags=re.IGNORECASE)
            
            if let == correct_letter:
                correct_text = opt_clean_body if opt_clean_body else "Alternativa correta conforme as diretrizes e raciocínio clínico apresentados."
            else:
                if opt_clean_body:
                    distractors_lines.append(f"- **Letra {let}**: {opt_clean_body}")
                else:
                    distractors_lines.append(f"- **Letra {let}**: Incorreta.")
                    
        por_que_certa = f"**Por que a Letra {correct_letter} é a Correta?**:\n{correct_text}"
        distratores_str = "**Análise dos Distratores**:\n" + "\n".join(distractors_lines) if distractors_lines else ""
    else:
        por_que_certa = ""
        distratores_str = ""
    
    # 5. Bibliografia (opcional)
    bib_raw = exp_dict.get("bibliography") or ""
    bib_clean = clean_html_to_markdown(bib_raw)
    bib_str = f"**Referências Bibliográficas**:\n{bib_clean}" if bib_clean else ""

    sections = [gabarito_header, pulo_gato]
    if raciocinio:
        sections.append(raciocinio)
    if por_que_certa:
        sections.append(por_que_certa)
    if distratores_str:
        sections.append(distratores_str)
    if bib_str:
        sections.append(bib_str)
        
    return "\n\n".join(sections)

def import_medway_har(har_path: str):
    print(f"[HAR] Lendo arquivo Medway: {har_path}")
    with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)

    questions = {}
    explanations = {}
    track_order = []
    track_title = "Aprova Medway Simulado"

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
            if "api/v3/track/" in url and "questions" in url:
                qs = data if isinstance(data, list) else (data.get("results") or data.get("questions") or [])
                for q in qs:
                    qid = str(q.get("id"))
                    if qid and qid not in track_order:
                        track_order.append(qid)
            elif "api/v3/questions/" in url and "text-explanation" in url:
                qid = url.split("questions/")[1].split("/")[0]
                explanations[qid] = data
            elif "api/v3/questions/" in url and not "text-explanation" in url and not "reaction" in url and not "comments" in url and not "atualization" in url:
                qid = data.get("id") if isinstance(data, dict) else None
                if qid:
                    questions[str(qid)] = data
            elif "api/v3/track/" in url and "fast" in url:
                if isinstance(data, dict) and data.get("name"):
                    track_title = data.get("name")
        except Exception:
            pass

    inst_code, inst_label = detect_inst_from_title(track_title)
    
    # Extrair se é simulado 1, 2, etc.
    sim_match = re.search(r"simulado\s*(\d+)", track_title, re.IGNORECASE)
    sim_num = sim_match.group(1) if sim_match else "1"
    source_file = f"MEDWAY {inst_code} 2026 AUTORAL SIMULADO {sim_num}"
    year = 2026

    print(f"\n==================================================")
    print(f"[PROCESSANDO MEDWAY] {track_title}")
    print(f"Instituição Identificada: {inst_code} ({inst_label})")
    print(f"Source File: {source_file}")
    print(f"Total de questões identificadas: {len(track_order)}")
    print(f"Total de explicações completas: {len(explanations)}")
    print(f"==================================================")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Remover lote autoral anterior se já existir com esse mesmo source_file
    cursor.execute("SELECT id FROM questions WHERE source_file = ? AND editorial_status = 'autoral'", (source_file,))
    old_ids = [r["id"] for r in cursor.fetchall()]
    if old_ids:
        placeholders = ",".join("?" * len(old_ids))
        cursor.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", old_ids)
        cursor.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", old_ids)
        cursor.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", old_ids)
        cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", old_ids)
        print(f"[BANCO] Removidas {len(old_ids)} questões autorais anteriores de {source_file}.")

    total_inserted = 0
    total_images = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for q_idx, qid in enumerate(track_order, start=1):
        q = questions.get(qid, {})
        exp = explanations.get(qid, {})
        
        raw_stem = q.get("content") or ""
        stem = clean_html_to_markdown(raw_stem)
        
        opts = q.get("options", [])
        is_discursive = bool(q.get("question_type") == "d" or len(opts) == 0)
        correct_letter = extract_gabarito(exp, opts) if not is_discursive else "A"
        golden_exp = format_medway_golden_explanation(exp, opts, correct_letter, is_discursive=is_discursive)

        # Tags e Área
        tags = [t.get("name") for t in q.get("tag", []) if t.get("name")]
        speciality = ""
        if isinstance(q.get("speciality"), list) and q.get("speciality"):
            speciality = q.get("speciality")[0].get("name", "")
        elif isinstance(q.get("speciality"), dict):
            speciality = q.get("speciality").get("name", "")
            
        topic = tags[0] if tags else (speciality if speciality else "Clínica Médica Geral")
        subtema = tags[1] if len(tags) > 1 else topic
        area = infer_area_from_tags(speciality, tags)

        cursor.execute("""
            INSERT INTO questions (
                source_file, source_number, year, institution_code, institution_label,
                topic, stem, correct_letter, missing_alts, comment_code,
                area, subtema, editorial_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_file,
            q_idx,
            year,
            inst_code,
            inst_label,
            topic,
            stem,
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
        if is_discursive:
            cursor.execute("""
                INSERT INTO alternatives (question_id, letter, text, is_correct)
                VALUES (?, 'A', 'Questão Dissertativa - Ver Padrão de Resposta no Comentário', 1)
            """, (new_q_id,))
        else:
            for opt in opts:
                let = opt.get("letter", "").upper()
                raw_opt_text = opt.get("content") or ""
                opt_text = clean_html_to_markdown(raw_opt_text)
                is_corr = 1 if let == correct_letter else 0
                cursor.execute("""
                    INSERT INTO alternatives (question_id, letter, text, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (new_q_id, let, opt_text, is_corr))

        # Explicação
        cursor.execute("""
            INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at)
            VALUES (?, ?, ?, ?)
        """, (new_q_id, golden_exp, now_iso, now_iso))

        # Imagens
        img_urls = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', stem)
        img_tags = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', raw_stem)
        obj_imgs = [img.get("url") for img in q.get("images", []) if isinstance(img, dict) and img.get("url")]
        all_imgs = list(dict.fromkeys(img_urls + img_tags + obj_imgs))
        for order_idx, img_url in enumerate(all_imgs):
            cursor.execute("""
                INSERT INTO question_images (question_id, file_path, order_index)
                VALUES (?, ?, ?)
            """, (new_q_id, img_url, order_idx))
            total_images += 1

    conn.commit()
    conn.close()

    print(f"\n==================================================")
    print(f"[SUCESSO] Inseridas {total_inserted} questões autorais da Medway ({inst_code})!")
    print(f"[SUCESSO] Total de imagens indexadas: {total_images}")
    print(f"==================================================")

if __name__ == "__main__":
    har_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wmors\Downloads\MEDWAYAUTORALUNICAMP.har"
    import_medway_har(har_path)
