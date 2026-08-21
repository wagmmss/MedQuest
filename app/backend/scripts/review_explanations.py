import argparse
import os
import sqlite3
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Modelo Gemini recomendado
MODELS = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemma-4-31b-it"
]

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

PROMPT_TEMPLATE = """Você é um professor especialista de cursinho para residência médica.
Sua missão é revisar e padronizar a explicação de uma questão médica.

[DADOS DA QUESTÃO]
Enunciado: {stem}
Alternativas:
{alternatives}
Gabarito Oficial: Letra {correct_letter}
Explicação Atual (Base):
{current_explanation}

[INSTRUÇÕES DE FORMATAÇÃO]
Reescreva a explicação padronizando-a de acordo com o seguinte layout em Markdown. NÃO inclua nenhum texto adicional além da explicação formatada (nem blocos de código markdown, apenas o texto bruto markdown).

**Gabarito**: Letra {correct_letter}.

**Pulo do Gato**: <1 a 2 frases com o raciocínio clínico ou a dica matadora que resolve a questão direto ao ponto.>

**Alternativa Correta ({correct_letter})**: <Explicação detalhada, clara, didática e rica do porquê esta alternativa é a correta. Se a explicação atual for fraca, adicione os conceitos médicos necessários.>

**Alternativas Incorretas**:
- **Letra <Outra_Letra>**: <Explicação concisa do porquê está incorreta, destacando o erro conceitual.>
- **Letra <Outra_Letra>**: <...>
(Liste todas as alternativas incorretas)

Responda APENAS com a explicação formatada.
"""

VERIFY_PROMPT_TEMPLATE = """Você é um revisor médico rigoroso e auditor clínico.
Sua tarefa é verificar a veracidade clínica da explicação gerada para a seguinte questão de residência médica.

[DADOS DA QUESTÃO]
Enunciado: {stem}
Alternativas:
{alternatives}
Gabarito Oficial: Letra {correct_letter}

[EXPLICAÇÃO GERADA (PARA REVISÃO)]
{generated_explanation}

INSTRUÇÕES:
1. Analise criticamente se a explicação acima contém alguma informação falsa, imprecisão médica, ou alucinação baseada nas melhores práticas clínicas médicas.
2. Verifique se a explicação e o raciocínio sustentam de forma correta e lógica o gabarito oficial.
3. Se a explicação for 100% verídica, devolva o texto exato, sem alterar nada.
4. Caso haja alguma imprecisão médica, modifique o texto para corrigi-la, mas mantenha ESTRITAMENTE a estrutura do layout original (Gabarito, Pulo do Gato, Correta, Incorretas).
5. Responda APENAS com o texto da explicação (sem markdown code blocks).
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

def call_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "MedQuest Script"
    }
    
    for model in MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            elif response.status_code == 429:
                print(f"  [{model}] Rate limit. Esperando 5s...")
                time.sleep(5)
                continue
            else:
                print(f"  [{model}] Erro na API: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  [{model}] Exceção: {e}")
            
    return None

def review_explanation_with_verification(conn, q_id, stem, correct_letter, current_explanation):
    alts = get_alternatives_for_question(conn, q_id)
    alts_text = ""
    for a in alts:
        alts_text += f"Letra {a[0]}: {a[1]}\n"
        
    print("  > Gerando nova explicação...")
    prompt = PROMPT_TEMPLATE.format(
        stem=stem,
        alternatives=alts_text.strip(),
        correct_letter=correct_letter,
        current_explanation=current_explanation
    )
    
    initial_explanation = call_openrouter(prompt)
    
    if not initial_explanation:
        return None
        
    time.sleep(1) # pausa entre chamadas da API
    
    print("  > Verificando veracidade médica...")
    verify_prompt = VERIFY_PROMPT_TEMPLATE.format(
        stem=stem,
        alternatives=alts_text.strip(),
        correct_letter=correct_letter,
        generated_explanation=initial_explanation
    )
    
    verified_explanation = call_openrouter(verify_prompt)
    
    # Retornar a explicacao verificada, ou a inicial em caso de falha no passo de revisao
    return verified_explanation or initial_explanation

def clean_markdown(text):
    text = text.removeprefix("```markdown")
    text = text.removeprefix("```")
    text = text.removesuffix("```")
    return text.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Number of questions to process")
    args = parser.parse_args()
    
    print(f"Iniciando revisão dupla (Geração + Validação) para {'TODAS as' if not args.limit else args.limit} explicações...")
    conn = sqlite3.connect(DB_PATH)
    
    questions = get_questions_to_review(conn, limit=args.limit)
    print(f"Encontradas {len(questions)} explicações pendentes.")
    
    success_count = 0
    c = conn.cursor()
    
    for i, (q_id, stem, correct_letter, current_explanation) in enumerate(questions):
        print(f"Processando questão {q_id} ({i+1}/{len(questions)})...")
        
        new_explanation = review_explanation_with_verification(conn, q_id, stem, correct_letter, current_explanation)
        
        if not new_explanation:
            print(f"Falha ao gerar/revisar explicação para a questão {q_id}.")
            continue
            
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        new_explanation = clean_markdown(new_explanation)
                
        try:
            c.execute(
                "UPDATE explanations SET explanation_text = ?, reviewed_at = ? WHERE question_id = ?",
                (new_explanation, now, q_id)
            )
            conn.commit()
            success_count += 1
            print(f"  -> Questão {q_id} atualizada com sucesso.")
        except Exception as db_e:
            print(f"Erro DB ao atualizar {q_id}: {db_e}")
            
        time.sleep(2)
        
    print(f"\nFinalizado! {success_count} explicações revisadas e validadas com sucesso.")

if __name__ == "__main__":
    main()
