import argparse
import os
import sqlite3
import time
import json
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Modelo DeepSeek
MODELS = [
    "deepseek-chat"
]

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")

BATCH_PROMPT = """Você é um professor especialista de cursinho para residência médica e auditor clínico rigoroso.
Sua missão é revisar, corrigir e padronizar as explicações de um lote de questões médicas.

[INSTRUÇÕES GERAIS]
1. Analise criticamente cada explicação base para corrigir informações falsas, imprecisões ou alucinações.
2. Formate CADA questão rigorosamente com o layout abaixo, sem blocos de código markdown.
3. Retorne um JSON válido contendo um array, onde cada objeto tem "question_id" (inteiro) e "explanation_markdown" (string com o texto formatado).

[LAYOUT OBRIGATÓRIO PARA CADA EXPLICAÇÃO]
**Gabarito**: Letra [Letra Correta].

**Pulo do Gato**: <1 a 2 frases com o raciocínio clínico ou a dica matadora que resolve a questão direto ao ponto.>

**Alternativa Correta ([Letra Correta])**: <Explicação detalhada, clara, didática e rica do porquê esta alternativa é a correta. Adicione os conceitos médicos necessários se a base for fraca.>

**Alternativas Incorretas**:
- **Letra [Outra_Letra]**: <Explicação concisa do porquê está incorreta, destacando o erro conceitual.>
(Liste todas as alternativas incorretas)

[QUESTÕES PARA PROCESSAR]
{questions_json}
"""

def get_questions_to_review(conn, limit=None):
    c = conn.cursor()
    query = """
        SELECT e.question_id, q.stem, q.correct_letter, e.explanation_text
        FROM explanations e
        JOIN questions q ON e.question_id = q.id
        WHERE e.reviewed_at IS NULL
    """
    if limit:
        query += f" LIMIT {limit}"
        
    return c.execute(query).fetchall()

def get_alternatives_for_question(conn, q_id):
    c = conn.cursor()
    return c.execute("SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (q_id,)).fetchall()

def call_deepseek_batch(prompt):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    retries = 0
    while retries < 5:
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError as je:
                        print(f"  [deepseek-chat] Erro ao parsear JSON: {je}")
                        print(f"  [deepseek-chat] Conteúdo bruto: {content[:500]}...")
                        # Pode ter retornado markdown de JSON (```json ... ```)
                        try:
                            clean_content = content.replace("```json", "").replace("```", "").strip()
                            return json.loads(clean_content)
                        except:
                            break
            elif response.status_code in (429, 503):
                print(f"  [deepseek-chat] Rate limit ou sobrecarga ({response.status_code}). Esperando 5s...")
                time.sleep(5)
                retries += 1
                continue
            else:
                print(f"  [deepseek-chat] Erro na API: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"  [deepseek-chat] Exceção: {e}")
            retries += 1
            time.sleep(5)
            
    return None

def clean_markdown(text):
    if not isinstance(text, str):
        return ""
    text = text.removeprefix("```markdown")
    text = text.removeprefix("```json")
    text = text.removeprefix("```")
    text = text.removesuffix("```")
    return text.strip()

def process_batch(conn, batch):
    print(f"  > Gerando e auditando explicações para lote de {len(batch)} questões...")
    
    questions_data = []
    for q_id, stem, correct_letter, current_explanation in batch:
        alts = get_alternatives_for_question(conn, q_id)
        alts_text = "\\n".join([f"Letra {a[0]}: {a[1]}" for a in alts])
        
        questions_data.append({
            "question_id": q_id,
            "stem": stem,
            "alternatives": alts_text,
            "correct_letter": correct_letter,
            "current_explanation": current_explanation
        })
        
    prompt = BATCH_PROMPT.format(questions_json=json.dumps(questions_data, ensure_ascii=False, indent=2))
    
    results = call_deepseek_batch(prompt)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Number of questions to process")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of questions per API call")
    args = parser.parse_args()
    
    print(f"Iniciando revisão OTIMIZADA (Lotes de {args.batch_size}) para {'TODAS as' if not args.limit else args.limit} explicações...")
    conn = sqlite3.connect(DB_PATH)
    
    questions = get_questions_to_review(conn, limit=args.limit)
    print(f"Encontradas {len(questions)} explicações pendentes.")
    
    success_count = 0
    c = conn.cursor()
    
    for i in range(0, len(questions), args.batch_size):
        batch = questions[i:i + args.batch_size]
        print(f"Processando lote {i//args.batch_size + 1} (questões {i+1} a {min(i+args.batch_size, len(questions))} de {len(questions)})...")
        
        results = process_batch(conn, batch)
        
        if not results:
            print(f"Falha ao processar lote {i//args.batch_size + 1}.")
            time.sleep(1)
            continue
            
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extrai a lista caso a API tenha envelopado em um objeto {"explanations": [...]}
        if isinstance(results, dict):
            # Tenta pegar o primeiro valor que seja uma lista
            for val in results.values():
                if isinstance(val, list):
                    results = val
                    break
            else:
                # Se não achou lista, empacota num array
                results = [results]
                
        for item in results:
            if not isinstance(item, dict):
                continue
            q_id = item.get("question_id")
            new_explanation = clean_markdown(item.get("explanation_markdown", ""))
            
            if q_id and new_explanation:
                try:
                    c.execute(
                        "UPDATE explanations SET explanation_text = ?, reviewed_at = ? WHERE question_id = ?",
                        (new_explanation, now, q_id)
                    )
                    success_count += 1
                    print(f"  -> Questão {q_id} atualizada com sucesso.")
                except Exception as db_e:
                    print(f"Erro DB ao atualizar {q_id}: {db_e}")
                    
        conn.commit()
        # Removido sleep longo para acelerar
        time.sleep(0.5)
        
    print(f"\\nFinalizado! {success_count} explicações revisadas e validadas com sucesso.")

if __name__ == "__main__":
    main()
