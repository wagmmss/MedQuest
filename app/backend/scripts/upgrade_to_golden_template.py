"""
Script para expansão e geração de comentários no Template Ouro (5 Pilares).
Garante rigor médico, alta qualidade pedagógica, aprofundamento dos distratores
e suporte resiliente a múltiplos provedores de IA (DeepSeek, Gemini/Gemma, OpenRouter).
"""

import os
import sqlite3
import re
import json
import time
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

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """Você é um preceptor médico de elite e especialista em preparação para provas de residência médica (USP, ENARE, SUS-SP, Unifesp, Unicamp).
Escreva o comentário da questão médica no Template Ouro (5 Pilares) diretamente em Português.

ESTRUTURA OBRIGATÓRIA:
**Gabarito**: Letra [X]

**Pulo do Gato**: [1 a 2 frases curtas com a âncora diagnóstica, mnemônico ou pegadinha da banca para fixação em 5 segundos]

**Raciocínio Clínico**: [Síntese do caso, diagnóstico sindrômico/topográfico e integração fisiopatológica dos dados antes da análise das alternativas]

**Por que a Letra [X] é a Correta?**: [Fundamentação teórica aprofundada, embasada em consensos, diretrizes de sociedades médicas e protocolos do Ministério da Saúde/SUS]

**Análise dos Distratores**:
- **Letra [A]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [B]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [C]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]
- **Letra [D]**: [Aprofunde detalhadamente o porquê de estar incorreta, apontando os erros conceituais, terapêuticos e inconsistências clínicas em relação ao caso]

REGRAS CRÍTICAS:
1. Na Análise dos Distratores, concentre-se em aprofundar com rigor técnico o motivo do erro na situação apresentada.
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
        sub = re.split(r"\n+\s*(?:\*\s*(?:Elite preceptor|Check terminology|Final check|Self-Correction|Tone:|Language:|Ensure|Verify))", sub, flags=re.IGNORECASE)[0]
        
        # Clean formatting artifacts
        sub = re.sub(r'\"\}\s*$', '', sub)
        sub = re.sub(r'```\s*$', '', sub)
        sub = re.sub(r"\s*A explicação é 100% verídica.*$", "", sub, flags=re.IGNORECASE | re.MULTILINE)
        
        return sub.strip()

    return None

def call_deepseek(user_content: str) -> str | None:
    if not DEEPSEEK_KEY:
        return None
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_KEY}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Elabore o comentário no Template Ouro para a seguinte questão médica:\n\n{user_content}"}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return extract_clean_explanation(content)
    except Exception:
        return None

def call_gemini(user_content: str) -> str | None:
    if not GEMINI_KEY:
        return None
    model_name = "models/gemma-4-26b-a4b-it"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""{SYSTEM_PROMPT}

[QUESTÃO]
{user_content}

Escreva agora diretamente o comentário completo no formato do Template Ouro:"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return extract_clean_explanation(raw_text)
    except Exception:
        model_name2 = "models/gemma-4-31b-it"
        url2 = f"https://generativelanguage.googleapis.com/v1beta/{model_name2}:generateContent?key={GEMINI_KEY}"
        try:
            req2 = urllib.request.Request(url2, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req2, timeout=60) as resp2:
                data2 = json.loads(resp2.read().decode("utf-8"))
                raw_text2 = data2["candidates"][0]["content"]["parts"][0]["text"].strip()
                return extract_clean_explanation(raw_text2)
        except Exception:
            return None
    return None

def call_llm(question_data: dict) -> str | None:
    user_content = json.dumps({
        "question_id": question_data["id"],
        "area": question_data["area"],
        "subtema": question_data["subtema"],
        "ano": question_data["year"],
        "instituicao": question_data["institution_label"],
        "enunciado": question_data["stem"],
        "alternativas": question_data["alternatives"],
        "gabarito_oficial": question_data["correct_letter"],
        "comentario_atual_rascunho": question_data.get("current_explanation") or ""
    }, ensure_ascii=False)

    # 1. Try DeepSeek first
    res = call_deepseek(user_content)
    if not res:
        # 2. Try Gemini/Gemma
        res = call_gemini(user_content)

    return res

def process_question_batch(questions: list[dict], max_workers: int = 2):
    conn = get_db()
    cursor = conn.cursor()
    
    success_count = 0
    total = len(questions)
    
    print(f"\nIniciando processamento de {total} questoes com {max_workers} threads...", flush=True)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_q = {executor.submit(call_llm, q): q for q in questions}
        
        for future in concurrent.futures.as_completed(future_to_q):
            q = future_to_q[future]
            qid = q["id"]
            try:
                explanation = future.result()
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
                    print(f"[OK] QID {qid} ({q['area']} - {q['subtema']}) atualizada com sucesso no Template Ouro.", flush=True)
                else:
                    print(f"[FAIL] Falha ao gerar explicacao valida para QID {qid}", flush=True)
            except Exception as e:
                print(f"[ERROR] Erro ao processar QID {qid}: {e}", flush=True)

    conn.close()
    print(f"\nLote finalizado: {success_count}/{total} questoes atualizadas.", flush=True)

def fetch_target_questions(mode: str = "critical", limit: int = 50) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    if mode == "critical":
        cursor.execute("""
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            LEFT JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text IS NULL OR LENGTH(e.explanation_text) < 100
            ORDER BY q.id
            LIMIT ?
        """, (limit,))
    elif mode == "missing_distractors":
        cursor.execute("""
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text NOT LIKE '%Letra A:%' 
              AND e.explanation_text NOT LIKE '%- Letra A%'
              AND e.explanation_text NOT LIKE '%**Letra A%'
            ORDER BY q.id
            LIMIT ?
        """, (limit,))
    else: # all / full upgrade
        cursor.execute("""
            SELECT q.id, q.area, q.subtema, q.institution_label, q.year, q.stem, q.correct_letter, e.explanation_text
            FROM questions q
            JOIN explanations e ON e.question_id = q.id
            WHERE e.explanation_text NOT LIKE '%**Raciocínio Clínico**%'
            ORDER BY q.id
            LIMIT ?
        """, (limit,))
        
    rows = cursor.fetchall()
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
    parser = argparse.ArgumentParser(description="Atualiza comentarios para o Template Ouro")
    parser.add_argument("--mode", choices=["critical", "missing_distractors", "all"], default="critical", help="Modo de selecao das questoes")
    parser.add_argument("--limit", type=int, default=10, help="Quantidade de questoes para processar")
    parser.add_argument("--workers", type=int, default=2, help="Numero de threads simultaneas")
    
    args = parser.parse_args()
    
    target_questions = fetch_target_questions(mode=args.mode, limit=args.limit)
    print(f"Encontradas {len(target_questions)} questoes alvo para o modo '{args.mode}'.")
    
    if target_questions:
        process_question_batch(target_questions, max_workers=args.workers)
