import json
import re
import sys
import os

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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

def format_to_golden_template(q):
    # 1. Gabarito
    correct_letter = "?"
    answers = q.get("answers", [])
    for idx, ans in enumerate(answers):
        if ans.get("rightAnswer"):
            correct_letter = chr(65 + idx)
            break
            
    is_nulled = q.get("nulled", False)
    nulled_reason = q.get("nulledReason") or ""
    
    # 2. Pulo do Gato (from takeHomeMessage)
    thm = q.get("takeHomeMessage", "").strip()
    # Remove markdown header if present
    thm_clean = re.sub(r"^#+\s*Take\s*home\s*message:?\s*", "", thm, flags=re.IGNORECASE).strip()
    
    # 3. Raciocínio Clínico (from comment)
    raw_comment = q.get("comment", "").strip()
    # Clean video thumbnails: ![video-tag-https://...](...)
    clean_comment = re.sub(r"!\[video-tag-[^\]]*\]\([^\)]+\)", "", raw_comment).strip()
    clean_comment = re.sub(r"^#+\s*Coment[aá]rio:?\s*", "", clean_comment, flags=re.IGNORECASE).strip()
    
    # 4. Alternativas e Distratores
    correct_explanation = ""
    distractors_lines = []
    
    for idx, ans in enumerate(answers):
        let = chr(65 + idx)
        ans_comment = ans.get("comment", "") or ""
        # Strip html tags from comment if any
        ans_comment_clean = re.sub(r"<[^>]+>", " ", ans_comment).strip()
        ans_comment_clean = re.sub(r"\s+", " ", ans_comment_clean).strip()
        
        if ans.get("rightAnswer"):
            correct_explanation = ans_comment_clean
        else:
            if ans_comment_clean:
                distractors_lines.append(f"- **Letra {let}**: {ans_comment_clean}")
            else:
                distractors_lines.append(f"- **Letra {let}**: Incorreta.")
                
    # Build final golden template
    gabarito_header = f"**Gabarito**: Letra {correct_letter}"
    if is_nulled:
        gabarito_header += f" (ANULADA: {nulled_reason})"
        
    pulo_gato = f"**Pulo do Gato**:\n{thm_clean}" if thm_clean else "**Pulo do Gato**:\nFoco no diagnóstico sindrômico e na correlação clínica dos achados."
    raciocinio = f"**Raciocínio Clínico**:\n{clean_comment}" if clean_comment else ""
    
    por_que_certa = f"**Por que a Letra {correct_letter} é a Correta?**:\n{correct_explanation}" if correct_explanation else f"**Por que a Letra {correct_letter} é a Correta?**:\nAlternativa condizente com a conduta preconizada para o quadro."
    
    distratores_str = "**Análise dos Distratores**:\n" + "\n".join(distractors_lines) if distractors_lines else ""
    
    sections = [gabarito_header, pulo_gato]
    if raciocinio:
        sections.append(raciocinio)
    sections.append(por_que_certa)
    if distratores_str:
        sections.append(distratores_str)
        
    return "\n\n".join(sections)

print("=== EXEMPLO DA QUESTAO 1 NO TEMPLATE OURO ===")
print(format_to_golden_template(all_questions[0]))
print("\n" + "="*50 + "\n")
print("=== EXEMPLO DA QUESTAO 6 NO TEMPLATE OURO ===")
print(format_to_golden_template(all_questions[5]))
