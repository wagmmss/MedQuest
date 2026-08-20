import sqlite3
import argparse
import requests
import json
import time
from datetime import datetime, timezone
import os

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={API_KEY}"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

PROMPT_TEMPLATE = """
Você é um professor experiente de cursinho para residência médica.
Vou te fornecer uma lista de questões médicas de múltipla escolha. 
Para cada questão, eu já informarei qual é a alternativa correta.
A sua tarefa é redigir um comentário direto, focado e explicativo (com cerca de 100 a 200 palavras por questão) justificando o porquê a alternativa correta é a verdadeira e por que as outras opções estão incorretas.
Não mencione que a resposta foi fornecida a você. Escreva o comentário como um professor, com tom didático e focado no 'pulo do gato' da questão. Gere explicações (200 palavras no máximo) com um tom didático, iniciando com 'Pulo do gato:' seguido das opções corretas e incorretas. NUNCA utilize aspas duplas dentro do texto gerado (use apenas aspas simples) para não quebrar a formatação do JSON.

Formate a sua saída estritamente em JSON, utilizando a seguinte estrutura:

{
  "explanations": [
    {
      "question_id": <ID_DA_QUESTAO>,
      "explanation_text": "<O_SEU_COMENTARIO_PROFISSIONAL_AQUI>"
    }
  ]
}

Abaixo estão as questões para você comentar:

{questions_block}
"""

def get_questions_without_explanations(conn, limit=None):
    c = conn.cursor()
    query = """
        SELECT id, stem, correct_letter 
        FROM questions 
        WHERE id NOT IN (SELECT question_id FROM explanations)
    """
    if limit:
        query += f" LIMIT {limit}"
        
    return c.execute(query).fetchall()

def get_alternatives_for_question(conn, q_id):
    c = conn.cursor()
    return c.execute("SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (q_id,)).fetchall()

def generate_batch(conn, questions_batch):
    # Prepare prompt block
    questions_block = ""
    for q in questions_batch:
        q_id, stem, correct_letter = q
        alts = get_alternatives_for_question(conn, q_id)
        
        questions_block += f"--- Questão ID: {q_id} ---\n"
        questions_block += f"Enunciado: {stem}\n"
        for a in alts:
            questions_block += f"Alternativa {a[0]}: {a[1]}\n"
        questions_block += f"Gabarito Correto: Letra {correct_letter}\n\n"
        
    prompt = PROMPT_TEMPLATE.replace("{questions_block}", questions_block)
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Parse gemini response
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw_text)
        return data.get("explanations", [])
    except Exception as e:
        print(f"Erro ao comunicar com a API ou parsear JSON: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print("Resposta da API:", response.text)
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of questions to process")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size per prompt")
    args = parser.parse_args()
    
    print(f"Iniciando geração para {args.limit} questões (Lotes de {args.batch_size})...")
    conn = sqlite3.connect(DB_PATH)
    
    questions = get_questions_without_explanations(conn, limit=args.limit)
    print(f"Encontradas {len(questions)} questões sem comentário.")
    
    success_count = 0
    c = conn.cursor()
    
    for i in range(0, len(questions), args.batch_size):
        batch = questions[i:i+args.batch_size]
        print(f"Enviando lote de {len(batch)} questões...")
        
        results = generate_batch(conn, batch)
        
        if not results:
            print("Lote falhou ou não retornou dados estruturados.")
            continue
            
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        for exp in results:
            q_id = exp.get("question_id")
            text = exp.get("explanation_text")
            
            if q_id and text:
                try:
                    c.execute(
                        "INSERT OR REPLACE INTO explanations (question_id, explanation_text, generated_at) VALUES (?, ?, ?)",
                        (q_id, text, now)
                    )
                    success_count += 1
                except Exception as db_e:
                    print(f"Erro DB ao inserir {q_id}: {db_e}")
                    
        conn.commit()
        
        # Respeitar limites da API (Gemini Free: 15 RPM max, pause 5s)
        time.sleep(5)
        
    print(f"\nFinalizado! {success_count} comentários gerados com sucesso.")

if __name__ == "__main__":
    main()
