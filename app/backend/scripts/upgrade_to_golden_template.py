"""
Script para expansão e geração de comentários no Template Ouro (5 Pilares).
Garante rigor médico, alta qualidade pedagógica, aprofundamento dos distratores
e processamento concorrente multi-chave (Google AI / Gemma / Gemini).
"""

import os
import sqlite3
import re
import json
import time
import itertools
from datetime import datetime, timezone
import concurrent.futures
import urllib.request
import urllib.error

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def load_env_vars():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_env_vars()

raw_keys = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not API_KEYS:
    print("[AVISO] Nenhuma chave GEMINI_API_KEYS encontrada no .env")
else:
    print(f"[CONFIG] {len(API_KEYS)} chaves Google AI carregadas para processamento concorrente.")

key_cycle = itertools.cycle(API_KEYS)

SYSTEM_PROMPT = """Você é um preceptor médico de elite e especialista em preparação para provas de residência médica (USP, ENARE, SUS-SP, Unifesp, Unicamp).
Escreva diretamente em Português o comentário no Template Ouro (5 Pilares).
NÃO inclua notas ou raciocínio em inglês. Comece imediatamente com **Gabarito**:

[EXEMPLO DE ESTRUTURA PADRÃO]
**Gabarito**: Letra [X]

**Pulo do Gato**: [Âncora diagnóstica, mnemônico, síntese prática de alta relevância ou regras de decisão essenciais para a questão. Não precisa se limitar a 1 ou 2 frases; o foco primordial é máxima relevância clínica e valor pedagógico/prático para a prova]

**Raciocínio Clínico**: [Síntese do caso, diagnóstico sindrômico/topográfico e integração fisiopatológica dos dados antes da análise das alternativas]

**Por que a Letra [X] é a Correta?**: [Fundamentação teórica aprofundada, embasada em consensos, diretrizes de sociedades médicas e protocolos do Ministério da Saúde/SUS]

**Análise dos Distratores**:
- **Letra [A]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [B]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [C]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [D]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]

REGRAS CRÍTICAS:
1. Na Análise dos Distratores, concentre-se em aprofundar com rigor técnico o motivo do erro na situação clínica apresentada.
2. Se a questão for do tipo "Assinale a INCORRETA" ou "EXCETO", adapte o cabeçalho para: "**Por que a Letra [X] é a Incorreta (Gabarito)?**" e analise as opções verdadeiras sob "**Análise das Alternativas Verdadeiras**".
3. NUNCA inclua metatextos ou notas da IA no final (ex: "Explicação 100% verídica", "Sou uma IA", "Prompt").
4. Use português médico brasileiro padrão (CIVD e não DIC; plaquetopenia/trombocitopenia; obstrutiva e não obstructiva).
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def extract_clean_explanation(raw_text: str) -> str | None:
    if not raw_text:
        return None
    
    # 1. Match between explicit tags if present
    tag_m = re.search(r"\[INICIO_COMENTARIO\]([\s\S]*?)\[FIM_COMENTARIO\]", raw_text, re.IGNORECASE)
    if tag_m:
        clean = tag_m.group(1).strip()
        clean = re.sub(r"\s*A explicação é 100% verídica.*$", "", clean, flags=re.IGNORECASE | re.MULTILINE).strip()
        return clean

    # 2. Match from **Gabarito**:
    gabarito_pos = raw_text.find("**Gabarito**:")
    if gabarito_pos == -1:
        gabarito_pos = raw_text.find("Gabarito:")
        
    if gabarito_pos != -1:
        sub = raw_text[gabarito_pos:]
        
        # Stop at trailing checklist if any
        sub = re.split(r"\n+\s*(?:\*\s*(?:Elite preceptor|Check terminology|Final check|Self-Correction|Tone:|Language:|Ensure|Verify|Refining))", sub, flags=re.IGNORECASE)[0]
        
        # Clean formatting artifacts
        sub = re.sub(r'\"\}\s*$', '', sub)
        sub = re.sub(r'```\s*$', '', sub)
        sub = re.sub(r"\s*A explicação é 100% verídica.*$", "", sub, flags=re.IGNORECASE | re.MULTILINE)
        
        return sub.strip()

    return None

def call_google_ai(question_data: dict, primary_key: str) -> str | None:
    q_str = f"ID: {question_data['id']}\nÁrea: {question_data['area']} | Subtema: {question_data['subtema']}\nEnunciado: {question_data['stem']}\nGabarito Oficial: {question_data['correct_letter']}\nAlternativas: {json.dumps(question_data['alternatives'], ensure_ascii=False)}"
    prompt = f"{SYSTEM_PROMPT}\n\n[QUESTÃO A COMENTAR]\n{q_str}\n\nEscreva agora o comentário completo iniciando diretamente com **Gabarito**:"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    body = json.dumps(payload).encode("utf-8")
    
    # Try primary key, then fallback keys
    candidate_keys = [primary_key] + [k for k in API_KEYS if k != primary_key][:2]
    
    for k in candidate_keys:
        for model_name in ["models/gemma-4-26b-a4b-it", "models/gemma-4-31b-it"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={k}"
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=50) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    res = extract_clean_explanation(raw_text)
                    if res and len(res) > 150:
                        return res
            except Exception:
                time.sleep(1)
                continue
                
    return None

def process_single_question(q: dict) -> tuple[int, str | None]:
    api_key = next(key_cycle)
    result = call_google_ai(q, api_key)
    return q["id"], result

def process_question_batch(questions: list[dict], max_workers: int = 6):
    conn = get_db()
    cursor = conn.cursor()
    
    success_count = 0
    total = len(questions)
    
    print(f"\nIniciando processamento de {total} questões usando {len(API_KEYS)} chaves com {max_workers} threads simultâneas...", flush=True)
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_q = {executor.submit(process_single_question, q): q for q in questions}
        
        for idx, future in enumerate(concurrent.futures.as_completed(future_to_q), 1):
            q = future_to_q[future]
            qid = q["id"]
            try:
                _, explanation = future.result()
                if explanation and len(explanation) > 150:
                    now = datetime.now(timezone.utc).isoformat()
                    cursor.execute("""
                        INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(question_id) DO UPDATE SET
                            explanation_text = excluded.explanation_text,
                            reviewed_at = excluded.reviewed_at
                    """, (qid, explanation, now, now))
                    conn.commit()
                    success_count += 1
                    elapsed = time.time() - start_time
                    print(f"[{idx}/{total}] [OK] QID {qid} ({q['area']} - {q['subtema'][:30]}) atualizada. (Tempo decorrido: {elapsed:.1f}s)", flush=True)
                else:
                    print(f"[{idx}/{total}] [FAIL] Falha ao gerar explicação válida para QID {qid}", flush=True)
            except Exception as e:
                print(f"[{idx}/{total}] [ERROR] Erro no processamento de QID {qid}: {e}", flush=True)

    conn.close()
    total_time = time.time() - start_time
    print(f"\nLote finalizado com sucesso: {success_count}/{total} questões atualizadas no Template Ouro em {total_time:.1f}s!", flush=True)

def fetch_target_questions(mode: str = "critical", limit: int = None) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    if mode == "critical":
        # Missing explanations OR corrupted placeholders OR unstructured text
        query = """
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            LEFT JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text IS NULL 
               OR LENGTH(e.explanation_text) < 100
               OR e.explanation_text NOT LIKE '%**Pulo do Gato**%'
               OR (e.explanation_text NOT LIKE '%Letra A%' AND e.explanation_text NOT LIKE '%- Letra A%')
            ORDER BY q.id
        """
    elif mode == "missing_distractors":
        query = """
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text NOT LIKE '%Letra A:%' 
              AND e.explanation_text NOT LIKE '%- Letra A%'
              AND e.explanation_text NOT LIKE '%**Letra A%'
            ORDER BY q.id
        """
    else: # all
        query = """
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text NOT LIKE '%**Raciocínio Clínico**%'
            ORDER BY q.id
        """
        
    if limit:
        query += f" LIMIT {limit}"
        
    rows = cursor.execute(query).fetchall()
    questions = []
    
    for r in rows:
        qid = r["id"]
        cursor.execute("SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,))
        alts = [{"letter": a["letter"], "text": a["text"]} for a in cursor.fetchall()]
        
        questions.append({
            "id": qid,
            "area": r["area"],
            "subtema": r["subtema"],
            "institution_label": r["institution_label"],
            "year": r["year"],
            "stem": r["stem"],
            "correct_letter": r["correct_letter"],
            "alternatives": alts,
            "current_explanation": r["explanation_text"]
        })
        
    conn.close()
    return questions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Atualiza comentários para o Template Ouro multi-chave")
    parser.add_argument("--mode", choices=["critical", "missing_distractors", "all"], default="critical", help="Modo de seleção")
    parser.add_argument("--limit", type=int, default=None, help="Limite de questões (None para todas do modo)")
    parser.add_argument("--workers", type=int, default=6, help="Número de threads simultâneas")
    
    args = parser.parse_args()
    
    target_questions = fetch_target_questions(mode=args.mode, limit=args.limit)
    print(f"Encontradas {len(target_questions)} questões alvo para o modo '{args.mode}'.")
    
    if target_questions:
        process_question_batch(target_questions, max_workers=args.workers)
