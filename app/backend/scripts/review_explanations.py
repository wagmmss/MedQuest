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

import concurrent.futures

BATCH_PROMPT = """Revise e padronize as explicações destas questões médicas.
Corrija erros e alucinações. Formate exatamente como abaixo, sem blocos markdown extras.
Retorne APENAS um JSON com array de objetos: {{"question_id": int, "explanation_markdown": str}}.

[LAYOUT]
**Gabarito**: Letra [X].

**Pulo do Gato**: <Dica matadora direta>

**Alternativa Correta ([X])**: <Por que é correta>

**Alternativas Incorretas**:
- **Letra [Y]**: <Por que é incorreta>

[QUESTÕES]
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
                    except json.JSONDecodeError:
                        clean_content = content.replace("```json", "").replace("```", "").strip()
                        try:
                            return json.loads(clean_content)
                        except:
                            break
            elif response.status_code in (429, 503):
                time.sleep(5)
                retries += 1
                continue
            else:
                print(f"Erro {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            retries += 1
            time.sleep(5)
            
    return None

def process_batch(batch):
    print(f"  > Gerando para lote de {len(batch)} questões...")
    
    # Needs a separate connection for thread safety
    conn = sqlite3.connect(DB_PATH)
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
        
    prompt = BATCH_PROMPT.format(questions_json=json.dumps(questions_data, ensure_ascii=False))
    results = call_deepseek_batch(prompt)
    
    if results and isinstance(results, dict):
        if "explanations" in results:
            results = results["explanations"]
        elif "questions" in results:
            results = results["questions"]
    
    if results and isinstance(results, list):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        c = conn.cursor()
        for res in results:
            q_id = res.get("question_id")
            exp_md = res.get("explanation_markdown")
            if q_id and exp_md:
                c.execute("""
                    UPDATE explanations
                    SET explanation_text = ?, reviewed_at = ?
                    WHERE question_id = ?
                """, (exp_md, now, q_id))
                print(f"  -> Questão {q_id} atualizada.")
        conn.commit()
    conn.close()
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Number of questions to process")
    parser.add_argument("--batch-size", type=int, default=15, help="Number of questions per API call")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_PATH)
    questions = get_questions_to_review(conn, limit=args.limit)
    conn.close()
    print(f"Encontradas {len(questions)} pendentes. (Lotes: {args.batch_size}, Threads: {args.workers})")
    
    batches = [questions[i:i + args.batch_size] for i in range(0, len(questions), args.batch_size)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(process_batch, batches))
        
    print(f"\\nFinalizado! Lotes processados em paralelo.")

if __name__ == "__main__":
    main()
