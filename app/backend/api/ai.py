import json
import logging
import os
import re
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

# In-memory TTL cache for semantic search expansions (avoids redundant AI calls)
_search_cache = {}  # key: normalized query -> (timestamp, result)
_SEARCH_CACHE_TTL = 300  # 5 minutes
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def _clean_option_text(text: str) -> str:
    """Remove prefixos de alternativas como 'A) ', 'B - ', etc."""
    if not text:
        return ""
    return re.sub(r'^[A-Ea-e][\)\.\:\-]\s*', '', text).strip()


def _extract_pulo_do_gato(explanation: str) -> str:
    if not explanation:
        return ""
    match = re.search(r'\*\*Pulo do Gato\*\*:\s*([^\n\r]+(?:\n[^\n\r*]+)?)', explanation, re.IGNORECASE)
    if match:
        pulo = match.group(1).strip()
        return re.sub(r'\*\*', '', pulo)
    return ""


def _extract_why_wrong(explanation: str, wrong_letter: str, wrong_text: str) -> str:
    if not explanation:
        return ""
    if wrong_letter:
        pattern = rf'\*\*Alternativa[^\n]*\({re.escape(wrong_letter)}\)[^\n]*\*\*:\s*([^\n\r]+(?:\n[^\n\r*]+)?)'
        match = re.search(pattern, explanation, re.IGNORECASE)
        if not match:
            pattern2 = rf'\*\*Alternativa\s+{re.escape(wrong_letter)}[^\n]*\*\*:\s*([^\n\r]+(?:\n[^\n\r*]+)?)'
            match = re.search(pattern2, explanation, re.IGNORECASE)
        if match:
            why = match.group(1).strip()
            return re.sub(r'\*\*', '', why)
    return ""


def _extract_clinical_scenario(stem: str) -> str:
    if not stem:
        return ""
    cleaned_stem = re.sub(r'\s+', ' ', stem.strip())
    end_patterns = [
        r'(?:Diante disso|Diante do exposto|Diante desse quadro|Nesse momento|Nesse caso|Considerando o caso|Em relação ao caso|Sobre o caso descrito|Com base no caso|A respeito do quadro|Considerando as diretrizes|Com base nessas informações|Assinale a alternativa|Qual a conduta|Qual o diagnóstico|Qual é o diagnóstico|O diagnóstico mais provável|A melhor conduta|A conduta mais adequada|O manejo inicial|O exame padrão-ouro|O próximo passo).*$',
        r'(?:é correto afirmar|assinale a opção|assinale a assertiva|indique a conduta).*$'
    ]
    scenario = cleaned_stem
    for pat in end_patterns:
        m = re.search(pat, scenario, re.IGNORECASE)
        if m and m.start() > 30:
            scenario = scenario[:m.start()].strip()
            break
    scenario = re.sub(r'[\s,;:]+$', '', scenario).strip()
    if scenario and not scenario.endswith('.'):
        scenario += '.'
    return scenario


def _determine_question_type(stem: str, correct_text: str) -> str:
    combined = (stem + " " + correct_text).lower()
    if any(w in combined for w in ["conduta", "tratamento", "manejo", "terapêutica", "terapia", "medicação", "droga", "prescrever", "cirurgia"]):
        return "Conduta / Manejo indicado"
    if any(w in combined for w in ["diagnóstico", "hipótese diagnóstica", "quadro clínico sugere", "provável diagnóstico"]):
        return "Diagnóstico mais provável"
    if any(w in combined for w in ["exame", "solicitar", "investigação", "método complementar", "padrão-ouro"]):
        return "Investigação / Exame complementar"
    if any(w in combined for w in ["fisiopatologia", "mecanismo", "etiologia", "causa"]):
        return "Mecanismo / Fisiopatologia"
    return "Conceito Chave"


def _extract_medical_cloze_fallback(
    stem: str,
    correct_text: str,
    wrong_text: str,
    explanation: str = "",
    area: str = "",
    subtema: str = "",
    topic: str = "",
    correct_letter: str = "",
    wrong_letter: str = ""
) -> dict:
    """
    Gera um Cloze Flashcard didático, clínico e de alta qualidade baseado no erro médico,
    com contexto do caso, pergunta clínica focada, Pulo do Gato e análise de distrator.
    """
    correct_clean = _clean_option_text(correct_text)
    wrong_clean = _clean_option_text(wrong_text)
    
    scenario = _extract_clinical_scenario(stem)
    q_type = _determine_question_type(stem, correct_clean)
    pulo = _extract_pulo_do_gato(explanation)
    why_wrong = _extract_why_wrong(explanation, wrong_letter, wrong_clean)
    
    tag_subject = subtema or topic or area or "Caso Clínico"
    header = f"[{tag_subject}]"
    
    if scenario and len(scenario) > 20:
        front = f"{header} {scenario}\n\n👉 {q_type}: {{{{c1::{correct_clean}}}}}"
    else:
        front = f"{header}\n\n👉 {q_type}: {{{{c1::{correct_clean}}}}}"
        
    back_sections = []
    if pulo:
        back_sections.append(f"💡 Pulo do Gato:\n{pulo}")
        
    if why_wrong:
        back_sections.append(f"⚠️ Por que não '{wrong_clean}'?\n{why_wrong}")
    elif wrong_clean and wrong_clean.lower() != correct_clean.lower():
        back_sections.append(f"⚠️ Atenção ao distrator:\nA opção '{wrong_clean}' é incorreta para este quadro clínico.")
        
    if not pulo and not why_wrong and explanation:
        clean_exp = re.sub(r'(\*\*.*?\*\*|###.*?\n|##.*?\n)', '', explanation).strip()
        sentences = [s.strip() for s in re.split(r'[\.\n]+', clean_exp) if len(s.strip()) > 15]
        if sentences:
            back_sections.append(f"📚 Racional:\n{'. '.join(sentences[:2])}.")
            
    if not back_sections:
        back_sections.append(f"Gabarito Oficial:\n{correct_clean}")
        
    back = "\n\n".join(back_sections)
    context_str = f"{area} > {subtema}" if area and subtema else (area or subtema or "MedQuest Residência")
    
    return {
        "front": front,
        "back": back,
        "context": context_str
    }


def generate_cloze_flashcard(
    stem: str,
    correct_text: str,
    wrong_text: str,
    explanation: str = "",
    area: str = "",
    subtema: str = "",
    topic: str = "",
    correct_letter: str = "",
    wrong_letter: str = ""
) -> dict:
    """
    Gera um flashcard no formato Cloze de alta fidelidade médica.
    Se AI (Gemini ou Groq) estiver disponível, sintetiza com IA; caso contrário, executa o extrator determinístico.
    """
    correct_clean = _clean_option_text(correct_text)
    wrong_clean = _clean_option_text(wrong_text)

    prompt_wrong_section = f"""O QUE O ALUNO MARCOU (ERRADO):
{wrong_clean}

A RESPOSTA CORRETA (GABARITO):
{correct_clean}
""" if wrong_clean else f"""A RESPOSTA CORRETA (GABARITO):
{correct_clean}
"""

    prompt_back_instructions = f"""2. No campo "back":
   - Coloque o "💡 Pulo do Gato" (a regra de ouro médica / conduta padrão-ouro).
   - Explique "⚠️ Por que não '{wrong_clean}'?" apontando a armadilha do distrator que fez o aluno errar.
""" if wrong_clean else """2. No campo "back":
   - Coloque o "💡 Pulo do Gato" (a regra de ouro médica / conduta padrão-ouro e/ou explicação central).
"""

    prompt = f"""
Você é um preceptor médico especialista em preparação para residência médica (USP, SUS-SP, ENARE).
O aluno deseja criar um flashcard PERFEITO no formato Cloze (Repetição Espaçada FSRS) para esta questão.

ÁREA/TEMA: {area} - {subtema or topic}
ENUNCIADO DA QUESTÃO:
{stem}

{prompt_wrong_section}
COMENTÁRIO/EXPLICAÇÃO DO PROFESSOR:
{explanation or 'Nenhuma explicação fornecida.'}

DIRETRIZES OBRIGATÓRIAS:
1. No campo "front":
   - Inicie com a identificação do tema: "[{subtema or area or 'Caso Clínico'}]"
   - Resuma o caso clínico essencial do enunciado em 1-2 frases claras com os achados-chave.
   - Em seguida, coloque a pergunta clínica com a omissão cloze da resposta correta: "👉 Conduta / Diagnóstico: {{{{c1::{correct_clean}}}}}"
   - NUNCA mencione letras de alternativas (como A, B, C, D) no texto do flashcard.
{prompt_back_instructions}3. No campo "context": "{area} > {subtema or topic}"

Responda EXCLUSIVAMENTE em JSON válido:
{{
  "front": "[Tema] Resumo do caso clínico...\\n\\n👉 Pergunta clínica: {{{{c1::resposta}}}}",
  "back": "💡 Pulo do Gato:\\n...",
  "context": "{area} > {subtema or topic}"
}}
"""

    # Padrões que indicam que a IA gerou um card de baixa qualidade (formato legado)
    _LOW_QUALITY_PATTERNS = [
        "A alternativa correta era",
        "alternativa correta era",
        "Neste caso clínico, em vez de",
        "Para este quadro clínico,",
        "Você marcou",
    ]

    def _is_low_quality(card: dict) -> bool:
        front = card.get("front", "")
        back = card.get("back", "")
        # Rejeita se o front contém padrões genéricos
        for pat in _LOW_QUALITY_PATTERNS:
            if pat in front:
                return True
        # Rejeita se o front contém letras de alternativa no cloze (ex: {{c1::A) ...}})
        cloze_match = re.search(r'{{c1::(.*?)}}', front)
        if cloze_match:
            cloze_content = cloze_match.group(1)
            if re.match(r'^[A-Ea-e][\)\.\:\-]\s', cloze_content):
                return True
        # Rejeita se o back é apenas "Você marcou..." ou "Alternativa correta:"
        if back.startswith("Você marcou") or back == f"Alternativa correta: {cloze_match.group(1) if cloze_match else ''}.":
            return True
        return False

    def _sanitize_ai_card(card: dict) -> dict:
        """Remove letras de alternativa do cloze e limpa artefatos da IA."""
        front = card.get("front", "")
        back = card.get("back", "")
        # Remove letras dentro do cloze: {{c1::A) Texto}} -> {{c1::Texto}}
        front = re.sub(r'{{c1::[A-Ea-e][\)\.\:\-]\s*(.*?)}}', r'{{c1::\1}}', front)
        card["front"] = front
        card["back"] = back
        return card

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and not gemini_key.lower().startswith(("dummy", "test", "gsk_test")) and len(gemini_key) > 15:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                },
                "systemInstruction": {
                    "parts": [{"text": "Você responde apenas em JSON válido com as chaves front, back e context."}]
                }
            }
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = response.read().decode("utf-8")
                res_json = json.loads(res_data)
                result_str = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                result_str = result_str.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(result_str)
                if isinstance(parsed, dict) and "front" in parsed and "{{c1::" in parsed.get("front", ""):
                    if _is_low_quality(parsed):
                        logger.info("Gemini retornou card de baixa qualidade, usando fallback determinístico.")
                    else:
                        return _sanitize_ai_card(parsed)
        except Exception as e:
            logger.warning(f"Fallback para gerador local após falha no Gemini: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.lower().startswith(("dummy", "test", "gsk_test")) and len(groq_key) > 15:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você responde apenas em JSON válido com as chaves front, back e context."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=350,
                response_format={"type": "json_object"}
            )
            result_str = chat_completion.choices[0].message.content
            result_str = result_str.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(result_str)
            if isinstance(parsed, dict) and "front" in parsed and "{{c1::" in parsed.get("front", ""):
                if _is_low_quality(parsed):
                    logger.info("Groq retornou card de baixa qualidade, usando fallback determinístico.")
                else:
                    return _sanitize_ai_card(parsed)
        except Exception as e:
            logger.warning(f"Fallback para gerador local após falha no Groq: {e}")

    # Fallback médico determinístico de alta qualidade
    return _extract_medical_cloze_fallback(
        stem=stem,
        correct_text=correct_text,
        wrong_text=wrong_text,
        explanation=explanation,
        area=area,
        subtema=subtema,
        topic=topic,
        correct_letter=correct_letter,
        wrong_letter=wrong_letter
    )


def expand_search_query(query: str) -> list[str]:
    """
    Usa Gemini (ou fallback Groq) para expandir a pesquisa em 3 a 7 sinônimos ou termos relacionados.
    Retorna uma lista de strings. Se a IA falhar ou não houver chave, retorna apenas a query original.
    Resultados são cacheados por 5 minutos para evitar chamadas redundantes à IA.
    """
    cache_key = query.strip().lower()
    now = time.time()
    if cache_key in _search_cache:
        ts, cached_result = _search_cache[cache_key]
        if now - ts < _SEARCH_CACHE_TTL:
            return cached_result
        else:
            del _search_cache[cache_key]

    if len(_search_cache) > 500:
        stale_keys = [k for k, (ts, _) in _search_cache.items() if now - ts >= _SEARCH_CACHE_TTL]
        for k in stale_keys:
            del _search_cache[k]

    def _cache_and_return(terms):
        _search_cache[cache_key] = (now, terms)
        return terms

    prompt = f"""Você é um especialista médico focado em buscas. O usuário quer pesquisar o seguinte termo: "{query}"

Retorne um JSON contendo uma lista de strings (phrases). Esta lista deve conter o termo original e de 3 a 7 sinônimos, termos técnicos ou diagnósticos diferenciais intimamente ligados à pesquisa.

Exemplo para "pressao alta": ["pressao alta", "hipertensao", "has", "crise hipertensiva", "pressao arterial"]
Exemplo para "infarto": ["infarto", "iam", "isquemia miocardica", "sindrome coronariana", "supra de st"]

Responda APENAS com o JSON. Exemplo: {{ "terms": ["...", "..."] }}
"""

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                },
                "systemInstruction": {
                    "parts": [{"text": "Você responde apenas em JSON válido."}]
                }
            }
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = response.read().decode("utf-8")
                res_json = json.loads(res_data)
                result_str = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                result_str = result_str.replace("```json", "").replace("```", "").strip()
                data = json.loads(result_str)
                terms = data.get("terms", [])
                if terms and isinstance(terms, list):
                    return _cache_and_return(terms)
        except Exception as e:
            logger.error(f"Erro na expansão via Gemini: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você responde apenas em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            result_str = completion.choices[0].message.content
            data = json.loads(result_str)
            terms = data.get("terms", [])
            if terms and isinstance(terms, list):
                return _cache_and_return(terms)
        except Exception as e:
            logger.error(f"Erro na expansão via Groq: {e}")

    return _cache_and_return([query])


