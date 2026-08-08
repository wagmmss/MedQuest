import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

def generate_cloze_flashcard(stem: str, correct_text: str, wrong_text: str, explanation: str) -> dict:
    """
    Calls Groq to generate a Cloze flashcard based on the user's mistake.
    Returns a dict with {"front": "...", "back": "..."}
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback se não tiver chave (mock para desenvolvimento local)
        return {
            "front": f"Atenção: Você marcou '{wrong_text}' mas o correto é {{{{c1::{correct_text}}}}}.",
            "back": "Configure a GROQ_API_KEY no .env para gerar flashcards reais com IA."
        }

    client = Groq(api_key=api_key)
    
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

Responda EXCLUSIVAMENTE com um JSON válido no formato:
{{
  "front": "texto do flashcard com a omissão cloze",
  "back": "explicação curta do erro vs acerto"
}}
Não inclua markdown ````json ou nenhum texto fora das chaves do JSON.
"""

    try:
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
        # Remove potential markdown block formatting from Groq response
        result_str = result_str.replace("```json", "").replace("```", "").strip()
        return json.loads(result_str)
    except json.JSONDecodeError as e:
        logger.error(f"Erro no parse JSON da geração do flashcard: {e}\nRetorno: {result_str}")
        return {
            "front": f"A alternativa correta era {{{{c1::{correct_text}}}}}.",
            "back": "Houve um erro no parse da IA."
        }
    except Exception as e:
        logger.error(f"Erro na geração do flashcard: {e}")
        return {
            "front": f"A alternativa correta era {{{{c1::{correct_text}}}}}.",
            "back": "Houve um erro na geração via IA."
        }

def expand_search_query(query: str) -> list[str]:
    """
    Usa a IA para expandir a pesquisa em 3 a 7 sinônimos ou termos relacionados.
    Retorna uma lista de strings. Se a IA falhar ou não houver chave, retorna apenas a query original.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return [query]
        
    client = Groq(api_key=api_key)
    
    prompt = f"""Você é um especialista médico focado em buscas. O usuário quer pesquisar o seguinte termo: "{query}"

Retorne um JSON contendo uma lista de strings (phrases). Esta lista deve conter o termo original e de 3 a 7 sinônimos, termos técnicos ou diagnósticos diferenciais intimamente ligados à pesquisa.

Exemplo para "pressao alta": ["pressao alta", "hipertensao", "has", "crise hipertensiva", "pressao arterial"]
Exemplo para "infarto": ["infarto", "iam", "isquemia miocardica", "sindrome coronariana", "supra de st"]

Responda APENAS com o JSON. Exemplo: {{ "terms": ["...", "..."] }}
"""
    try:
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
        if not terms or not isinstance(terms, list):
            return [query]
            
        return terms
    except json.JSONDecodeError as e:
        logger.error(f"Erro no parse JSON da expansão de busca: {e}")
        return [query]
    except Exception as e:
        logger.error(f"Erro na expansão de busca: {e}")
        return [query]
