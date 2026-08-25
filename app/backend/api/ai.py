import json
import logging
import os
import re
import time

from api.gemini_pool import gemini_pool

logger = logging.getLogger(__name__)

# In-memory TTL cache for semantic search expansions (avoids redundant AI calls)
_search_cache = {}  # key: normalized query -> (timestamp, result)
_SEARCH_CACHE_TTL = 300  # 5 minutes
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")

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
    is_dummy_text = any(phrase in correct_clean.lower() for phrase in ["anote sua", "questao dissertativa", "questão dissertativa", "padrao de resposta", "padrão de resposta"])
    pulo = _extract_pulo_do_gato(explanation)
    
    if is_dummy_text:
        # Extrai resposta alvo do pulo do gato ou explicação
        if pulo and len(pulo) < 120:
            target_cloze = pulo
        else:
            target_cloze = "Ver Padrão de Resposta / Pulo do Gato"
    else:
        target_cloze = correct_clean

    scenario = _extract_clinical_scenario(stem)
    q_type = _determine_question_type(stem, target_cloze)
    why_wrong = _extract_why_wrong(explanation, wrong_letter, wrong_clean)
    
    tag_subject = subtema or topic or area or "Caso Clínico"
    header = f"[{tag_subject}]"
    
    if scenario and len(scenario) > 20:
        front = f"{header} {scenario}\n\n👉 {q_type}: {{{{c1::{target_cloze}}}}}"
    else:
        front = f"{header}\n\n👉 {q_type}: {{{{c1::{target_cloze}}}}}"
        
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

    # Tenta gerar via Gemini Pool (multi-chaves)
    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction="Você responde apenas em JSON válido com as chaves front, back e context.",
                json_mode=True,
                model=GEMINI_MODEL,
                timeout=8
            )
            result_str = resp.get("text", "").replace("```json", "").replace("```", "").strip()
            parsed = json.loads(result_str)
            if isinstance(parsed, dict) and "front" in parsed and "{{c1::" in parsed.get("front", ""):
                if _is_low_quality(parsed):
                    logger.info("Gemini retornou card de baixa qualidade, usando fallback determinístico.")
                else:
                    return _sanitize_ai_card(parsed)
        except Exception as e:
            logger.warning(f"Fallback para Groq/Local após falha no Gemini Pool: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.lower().startswith(("dummy", "test", "gsk_test")) and len(groq_key) > 15:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=10.0, max_retries=1)
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

    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction="Você responde apenas em JSON válido.",
                json_mode=True,
                model=GEMINI_MODEL,
                timeout=6
            )
            result_str = resp.get("text", "").replace("```json", "").replace("```", "").strip()
            data = json.loads(result_str)
            terms = data.get("terms", [])
            if terms and isinstance(terms, list):
                return _cache_and_return(terms)
        except Exception as e:
            logger.error(f"Erro na expansão via Gemini Pool: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=8.0, max_retries=1)
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


def ask_preceptor_ai(
    stem: str,
    alternatives: list,
    correct_letter: str,
    correct_text: str,
    user_letter: str = "",
    user_question: str = "",
    explanation: str = "",
    area: str = "",
    subtema: str = ""
) -> dict:
    """
    Atua como um Preceptor Médico Socrático especialista em provas de residência (USP, ENARE, SUS-SP).
    Responde às dúvidas do aluno com clareza, rigor científico e foco nas armadilhas da banca usando Gemini 3.7 Flash.
    """
    alts_formatted = "\n".join([
        f"{a.get('letter', '')}) {a.get('text', '')}"
        for a in alternatives
        if isinstance(a, dict)
    ])
    
    prompt = f"""Você é o Preceptor Clínico Virtual do MedQuest, especialista em preparação para residência médica de alto nível (USP, ENARE, SUS-SP).

ÁREA / TEMA: {area} - {subtema}
ENUNCIADO DA QUESTÃO:
{stem}

ALTERNATIVAS:
{alts_formatted}

GABARITO OFICIAL: Letra {correct_letter} ({correct_text})
RESPOSTA MARCADA PELO ALUNO: {f'Letra {user_letter}' if user_letter else 'Ainda não respondeu ou acertou'}
COMENTÁRIO BASE:
{explanation or 'Nenhum comentário adicional.'}

DÚVIDA / PEDIDO DO ALUNO:
{user_question or 'Por favor, explique o raciocínio clínico da questão, por que a correta é o padrão-ouro e onde está a armadilha do distrator.'}

INSTRUÇÕES DO PRECEPTOR:
1. Responda em tom encorajador, clínico, didático e direto ao ponto.
2. Foque no raciocínio fisiopatológico e na conduta padrão-ouro recomendada pelas diretrizes médicas.
3. Se o aluno marcou uma alternativa incorreta, aponte a pegadinha com precisão.
4. Finalize com uma '💡 Regra de Ouro' (1 frase memorável para a prova).
5. Formate a resposta em Markdown claro com tópicos destacados.
"""

    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction="Você é um preceptor médico de excelência que ensina raciocínio clínico para residência médica.",
                model=GEMINI_MODEL,
                timeout=12
            )
            text = resp.get("text", "").strip()
            if text:
                return {
                    "answer": text,
                    "model": resp.get("model", GEMINI_MODEL),
                    "source": "gemini"
                }
        except Exception as e:
            logger.error(f"Erro no preceptor IA via Gemini Pool: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.lower().startswith(("dummy", "test", "gsk_test")) and len(groq_key) > 15:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=12.0, max_retries=1)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você é um preceptor médico de excelência que ensina raciocínio clínico para residência médica."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=600
            )
            text = completion.choices[0].message.content.strip()
            if text:
                return {
                    "answer": text,
                    "model": "llama-3.3-70b-versatile",
                    "source": "groq"
                }
        except Exception as e:
            logger.error(f"Erro no preceptor IA via Groq: {e}")

    fallback_response = f"**Raciocínio Clínico Resumido**:\nO gabarito oficial é a Letra **{correct_letter}** ({correct_text}).\n\n"
    if explanation:
        fallback_response += f"**Comentário da Questão**:\n{explanation}\n\n"
    fallback_response += f"💡 **Regra de Ouro**: Em {subtema or area or 'questões clínicas'}, atente-se sempre aos critérios diagnósticos e às contraindicações específicas antes de definir a conduta."
    
    return {
        "answer": fallback_response,
        "model": "deterministic_fallback",
        "source": "fallback"
    }


def _extract_json_block(text: str) -> dict | None:
    """Extrai e faz parsing resiliente de JSON mesmo com markdown ou texto envolvente."""
    if not text:
        return None
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    
    match = re.search(r'(\{[\s\S]*\})', cleaned)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return None


def generate_study_prescription(
    weak_topics: list | None = None,
    distractors: list | None = None,
    at_risk_topics: list | None = None,
    target_institution: str | None = None
) -> dict:
    """
    Gera uma Prescrição Clínica de Estudo personalizada de alto rendimento usando Gemini 3.7 Flash.
    Analisa os tópicos de menor acurácia, as pegadinhas em que o aluno mais cai e os cards em risco de esquecimento.
    """
    institution_context = f"Instituição Alvo: {target_institution}\n" if target_institution else "Foco: Residência Médica Geral (USP, ENARE, SUS-SP)\n"
    
    weak_str = "\n".join([
        f"- {wt.get('topic') or wt.get('subtema')}: {wt.get('correct', 0)} acertos em {wt.get('attempts', 0)} questões ({round((wt.get('accuracy', 0))*100)}% acurácia)"
        for wt in (weak_topics or [])[:6]
    ]) or "Nenhum tópico crítico identificado."

    distractors_str = "\n".join([
        f"- Subtema '{d.get('subtema')}': Costuma marcar alternativa incorreta {d.get('wrong_choices', [{}])[0].get('letter', '?')} ({d.get('wrong_choices', [{}])[0].get('count', 0)}x)"
        for d in (distractors or [])[:4]
        if d.get('wrong_choices')
    ]) or "Nenhum distrator recorrente mapeado."

    at_risk_str = "\n".join([
        f"- {r.get('subtema')}: {r.get('items_count', 1)} cartões FSRS próximos do esquecimento"
        for r in (at_risk_topics or [])[:4]
    ]) or "Memória em dia para as revisões ativas."

    prompt = f"""Você é o Diretor Pedagógico e Preceptor Médico Chefe do MedQuest.
Gere uma "Prescrição Clínica de Estudo" personalizada para este médico residente.

{institution_context}
DIAGNÓSTICO DO ALUNO:
1. Tópicos de Baixo Rendimento:
{weak_str}

2. Padrões de Armadilhas / Distratores:
{distractors_str}

3. Tópicos com Risco de Esquecimento (FSRS):
{at_risk_str}

DIRETRIZES:
1. Faça um diagnóstico clínico e encorajador em 2-3 frases.
2. Defina o "Plano Tático em 3 Passos" com conceitos de alto rendimento para reverter os tópicos fracos.
3. Aponte a "Vacina contra Distratores" alertando sobre as pegadinhas mapeadas.
4. Conclua com a "Regra de Ouro Semanal".
5. Formate a resposta em Markdown limpo com ícones e bullet points.

Responda em formato estruturado.
"""

    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction="Você é o diretor pedagógico do MedQuest especialista em aprovação de residência médica.",
                model=GEMINI_MODEL,
                timeout=15
            )
            text = resp.get("text", "").strip()
            if text:
                return {
                    "prescription_markdown": text,
                    "model": resp.get("model", GEMINI_MODEL),
                    "source": "gemini"
                }
        except Exception as e:
            logger.error(f"Erro na prescrição de estudos via Gemini Pool: {e}")

    fallback_md = f"""### 🩺 Prescrição de Estudo Personalizada

**Diagnóstico Geral**:
Identificamos pontos de atenção imediatos em tópicos-chave. Com foco nos conceitos fisiopatológicos e diferenciação de condutas, sua pontuação terá um salto rápido.

**Plano Tático Imediato**:
- **Revisão Ativa**: Priorize realizar blocos de 15 questões dos seus temas com menor acurácia.
- **Atenção aos Distratores**: Redobre o cuidado com as alternativas que você mais assinala por impulso. Identifique palavras excludentes (*sempre*, *nunca*, *apenas*).
- **Consolidação FSRS**: Conclua as revisões ativas pendentes antes de iniciar questões inéditas.

💡 **Regra de Ouro**: A aprovação na residência médica é construída na correção minuciosa de cada erro. Entenda o porquê de cada distrator.
"""
    return {
        "prescription_markdown": fallback_md,
        "model": "deterministic_fallback",
        "source": "fallback"
    }


def synthesize_question_explanation(
    stem: str,
    alternatives: list,
    correct_letter: str,
    correct_text: str,
    area: str = "",
    subtema: str = ""
) -> dict:
    """
    Sintetiza um comentário médico estruturado e completo (Pulo do Gato, Raciocínio Clínico,
    Alternativa Correta, Distratores e Referências) para uma questão utilizando Gemini 3.7 Flash.
    """
    alts_formatted = "\n".join([
        f"{a.get('letter', '')}) {a.get('text', '')}"
        for a in alternatives
        if isinstance(a, dict)
    ])

    prompt = f"""Você é um professor especialista em provas de residência médica (USP, ENARE, SUS-SP).
Crie o comentário oficial perfeito para a seguinte questão de residência médica:

ÁREA: {area} | SUBTEMA: {subtema}
ENUNCIADO:
{stem}

ALTERNATIVAS:
{alts_formatted}

GABARITO: Letra {correct_letter} ({correct_text})

ESTRUTURA OBRIGATÓRIA DA RESPOSTA (JSON):
{{
  "pulo_do_gato": "Âncora diagnóstica, mnemônico, síntese prática de alta relevância ou regras de decisão essenciais para fixação imediata do conceito da questão (com o tamanho e profundidade necessários para máxima relevância).",
  "raciocinio_clinico": "Explicação clínica e fisiopatológica detalhada do quadro e critérios de diagnóstico/conduta.",
  "alternativa_correta": "Por que a alternativa {correct_letter} é a única correta de acordo com as diretrizes.",
  "distratores": [
    {{"letter": "Letra", "explanation": "Por que está errada e qual a pegadinha"}}
  ],
  "medical_references": "Diretrizes e consensos médicos de referência (ex: Diretriz SBC, Manual MS, FEBRASGO, etc.)"
}}
"""

    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction="Você responde exclusivamente em JSON válido.",
                json_mode=True,
                model=GEMINI_MODEL,
                timeout=15
            )
            parsed = _extract_json_block(resp.get("text", ""))
            if parsed and "pulo_do_gato" in parsed and "raciocinio_clinico" in parsed:
                # Monta a string estruturada em markdown
                distratores_md = "\n".join([
                    f"- **Alternativa ({d.get('letter')})**: {d.get('explanation')}"
                    for d in parsed.get("distratores", [])
                ])
                full_explanation = f"""**Gabarito Oficial**: Letra {correct_letter}

**Pulo do Gato**: {parsed.get('pulo_do_gato')}

**Raciocínio Clínico**:
{parsed.get('raciocinio_clinico')}

**Alternativa Correta ({correct_letter})**:
{parsed.get('alternativa_correta')}

**Análise dos Distratores**:
{distratores_md}
"""
                return {
                    "explanation_text": full_explanation.strip(),
                    "pulo_do_gato": parsed.get("pulo_do_gato"),
                    "medical_references": parsed.get("medical_references", "Diretrizes Médicas Brasileiras"),
                    "source": "gemini",
                    "model": resp.get("model", GEMINI_MODEL)
                }
        except Exception as e:
            logger.error(f"Erro na síntese de comentário via Gemini Pool: {e}")

    # Fallback estruturado
    fallback_text = f"""**Gabarito Oficial**: Letra {correct_letter}

**Pulo do Gato**: O padrão-ouro em {subtema or area or 'quadros semelhantes'} baseia-se na identificação precoce dos critérios clínicos e conduta conforme diretrizes vigentes.

**Alternativa Correta ({correct_letter})**:
A alternativa ({correct_letter}) apresenta a abordagem preconizada para o caso apresentado.
"""
    return {
        "explanation_text": fallback_text.strip(),
        "pulo_do_gato": f"Foco nos critérios de {subtema or area}.",
        "medical_references": "Consensos e Diretrizes das Sociedades Brasileiras de Especialidades.",
        "source": "fallback",
        "model": "deterministic_fallback"
    }


