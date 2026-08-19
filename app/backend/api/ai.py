import os
import json
import logging
import urllib.request
import urllib.error
import time

logger = logging.getLogger(__name__)

# In-memory TTL cache for semantic search expansions (avoids redundant AI calls)
_search_cache = {}  # key: normalized query -> (timestamp, result)
_SEARCH_CACHE_TTL = 300  # 5 minutes

def generate_cloze_flashcard(stem: str, correct_text: str, wrong_text: str, explanation: str) -> dict:
    """
    Calls Gemini (or fallback Groq) to generate a Cloze flashcard based on the user's mistake.
    Returns a dict with {"front": "...", "back": "..."}
    """
    prompt = f"""
Você é um tutor médico de alto nível focado na técnica de repetição espaçada (flashcards).
O aluno errou uma questão importante e você precisa criar um flashcard PERFEITO no formato Cloze.

ENUNCIADO DA QUESTÃO:
{stem}

O QUE O ALUNO MARCOU (ERRADO):
{wrong_text}

A RESPOSTA CORRETA:
{correct_text}

COMENTÁRIO/EXPLICAÇÃO:
{explanation or 'Nenhuma explicação fornecida.'}

REGRAS CRÍTICAS PARA O FLASHCARD:
1. Não copie o enunciado. Extraia APENAS o conceito nuclear (o "pulo do gato") que faria o aluno acertar.
2. O texto (front) deve ser direto, curto e objetivo (máximo de 2 a 3 linhas).
3. Esconda APENAS a palavra-chave crítica (ex: o nome do remédio, o diagnóstico, o achado clínico) usando a sintaxe exata: {{{{c1::palavra}}}}. Nunca esconda frases inteiras.
4. Jamais cite letras de alternativas (ex: "A alternativa B está correta").
5. Foque em contrastar o erro do aluno com o acerto. Exemplo de estrutura boa: "Na suspeita de X, a conduta não é Y (como você pensou), mas sim {{{{c1::Z}}}}."
6. No campo "back", forneça uma nota de rodapé super rápida (1 a 2 frases) explicando objetivamente POR QUE o erro do aluno estava errado com base na fisiologia/diretriz.
7. No campo "context", informe de forma extremamente curta a fonte dessa conduta ou um resumo simples (ex: "Diretriz SBC 2024" ou "Consenso Brasileiro").

Responda EXCLUSIVAMENTE com um JSON válido no formato:
{{
  "front": "texto do flashcard com a omissão cloze",
  "back": "explicação curta do erro vs acerto",
  "context": "fonte super curta da diretriz/conduta"
}}
Não inclua markdown ```json ou nenhum texto fora das chaves do JSON.
"""

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
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
            with urllib.request.urlopen(req) as response:
                res_data = response.read().decode("utf-8")
                res_json = json.loads(res_data)
                result_str = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                result_str = result_str.replace("```json", "").replace("```", "").strip()
                return json.loads(result_str)
        except Exception as e:
            logger.error(f"Erro na geração via Gemini: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você responde apenas em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            result_str = chat_completion.choices[0].message.content
            result_str = result_str.replace("```json", "").replace("```", "").strip()
            return json.loads(result_str)
        except Exception as e:
            logger.error(f"Erro na geração via Groq: {e}")

    # Fallback/Mock
    return {
        "front": f"A alternativa correta era {{{{c1::{correct_text}}}}}.",
        "back": f"Você marcou '{wrong_text}'."
    }

def expand_search_query(query: str) -> list[str]:
    """
    Usa Gemini (ou fallback Groq) para expandir a pesquisa em 3 a 7 sinônimos ou termos relacionados.
    Retorna uma lista de strings. Se a IA falhar ou não houver chave, retorna apenas a query original.
    Resultados são cacheados por 5 minutos para evitar chamadas redundantes à IA.
    """
    # Cache lookup (normalized key)
    cache_key = query.strip().lower()
    now = time.time()
    if cache_key in _search_cache:
        ts, cached_result = _search_cache[cache_key]
        if now - ts < _SEARCH_CACHE_TTL:
            return cached_result
        else:
            del _search_cache[cache_key]

    # Evict stale entries periodically (keep cache bounded)
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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
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
            with urllib.request.urlopen(req) as response:
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

def stream_explanation(stem: str, correct_text: str, wrong_text: str = None) -> list[str]:
    """
    Generator that yields explanation text chunk by chunk.
    """
    if wrong_text:
        context = f"O aluno marcou a alternativa: '{wrong_text}' que está INCORRETA.\nA alternativa CORRETA é: '{correct_text}'."
    else:
        context = f"A alternativa CORRETA é: '{correct_text}'."
        
    prompt = f"""Você é um professor padrão ouro de Medicina (residência USP). 
Explique de forma didática e muito rápida (máximo 2 parágrafos curtos) POR QUE a resposta correta está certa, focando no 'pulo do gato' clínico.
Se o aluno errou, aponte a principal pegadinha que o levou ao erro.

QUESTÃO: {stem}
{context}

Seja direto. Não inclua saudações. Use markdown leve (negrito)."""

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:streamGenerateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('"text":'):
                        # rudimentary parsing for gemini stream
                        # This is a bit brittle, but handles basic cases. A proper library is better.
                        try:
                            # extract text from JSON fragment
                            part = line_str[7:].strip().rstrip(',')
                            text = json.loads("{" + f'"text": {part}' + "}")["text"]
                            yield text
                        except:
                            pass
                return
        except Exception as e:
            logger.error(f"Erro no streaming Gemini: {e}")

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Seja direto, didático e use formatação markdown."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=300,
                stream=True
            )
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except Exception as e:
            logger.error(f"Erro no streaming Groq: {e}")
            
    yield "Nenhuma API de IA configurada para exibir explicação."


