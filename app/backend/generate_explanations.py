import os
import sys
import json
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

# ── Chave do Groq: variável de ambiente ou ../../.env ──────────────
env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)
api_key = os.environ.get("GROQ_API_KEY")
if not api_key and os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                api_key = line.strip().split("=", 1)[1]
                break

if not api_key:
    print("GROQ_API_KEY não encontrada (defina no .env)!")
    sys.exit(1)

# ── Configuração da API Groq ───────────────────────────────────────
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Modelos em ordem de qualidade. Cada um tem cota diária SEPARADA no Groq.
# O script usa o primeiro até esgotar a cota do dia e troca para o próximo sozinho.
MODELS = [
    "openai/gpt-oss-120b",      # 120B, melhor qualidade
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",     # reserva: mais fraco, mas cota alta
]
_model_idx = 0
# User-Agent de navegador é obrigatório (o Cloudflare do Groq bloqueia o padrão do Python).
HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}
SLEEP_BETWEEN = 5   # segundos entre questões (respeita ~12k tokens/min)


def call_groq(prompt, max_attempts=50):
    """Chama o Groq e devolve o texto. Troca de modelo quando a cota diária de um esgota;
    espera e re-tenta em limites de curta duração (por minuto)."""
    global _model_idx
    for _ in range(max_attempts):
        if _model_idx >= len(MODELS):
            raise RuntimeError("Todos os modelos esgotaram a cota diária. Tente novamente amanhã.")
        model = MODELS[_model_idx]
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }).encode("utf-8")
        try:
            req = urllib.request.Request(GROQ_URL, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                msg = ""
                try:
                    msg = e.read().decode("utf-8").lower()
                except Exception:
                    pass
                try:
                    wait = float(e.headers.get("retry-after", 20))
                except (TypeError, ValueError):
                    wait = 20.0
                # Cota diária esgotada (ou espera longa) -> troca de modelo.
                if "per day" in msg or "tpd" in msg or wait > 120:
                    print(f"    modelo {model} esgotou a cota diária — trocando de modelo.")
                    _model_idx += 1
                    continue
                # Limite por minuto -> espera e tenta o mesmo modelo.
                print(f"    limite por minuto em {model}, aguardando {wait:.0f}s...")
                time.sleep(wait + 1)
                continue
            if 500 <= e.code < 600:
                print(f"    erro {e.code} do servidor, aguardando 10s...")
                time.sleep(10)
                continue
            raise
    raise RuntimeError("Muitas tentativas seguidas de limite.")


def process_year(year, redo=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Modo normal: só as que faltam. Modo --redo: regenera TODAS do ano (sobrescreve),
    # útil para refazer com os modelos grandes as explicações feitas pelo modelo reserva.
    if redo:
        questions = cur.execute(
            """SELECT id, stem, correct_letter, area, subtema FROM questions
               WHERE year = ? AND missing_alts = 0 AND correct_letter IS NOT NULL ORDER BY id""",
            (year,),
        ).fetchall()
        print(f"Ano {year} [REGENERAR]: {len(questions)} questões serão refeitas.")
    else:
        questions = cur.execute(
            """SELECT id, stem, correct_letter, area, subtema FROM questions
               WHERE year = ? AND missing_alts = 0 AND correct_letter IS NOT NULL
               AND id NOT IN (SELECT question_id FROM explanations
                              WHERE explanation_text IS NOT NULL AND explanation_text != '')
               ORDER BY id""",
            (year,),
        ).fetchall()
        print(f"Ano {year}: {len(questions)} questões precisam de explicação.")

    for i, q in enumerate(questions):
        qid = q["id"]

        alts = cur.execute(
            "SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)
        ).fetchall()
        alts_text = "\n".join([f"{a['letter']}) {a['text']}" for a in alts])

        prompt = f"""Você é um professor médico especialista.
Analise a questão a seguir e explique de forma didática e detalhada por que a alternativa correta é a correta, e justifique brevemente os erros das demais alternativas. Use um tom encorajador.

Área: {q['area']} - {q['subtema']}
Enunciado: {q['stem']}

Alternativas:
{alts_text}

Alternativa Correta: {q['correct_letter']}"""

        print(f"[{i+1}/{len(questions)}] Gerando QID {qid}...")

        try:
            explanation = call_groq(prompt)
            now = datetime.now(timezone.utc).isoformat()
            cur.execute(
                """INSERT INTO explanations (question_id, explanation_text, generated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(question_id) DO UPDATE SET
                     explanation_text = excluded.explanation_text,
                     generated_at = excluded.generated_at""",
                (qid, explanation, now),
            )
            conn.commit()
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"    Erro no QID {qid}: {e}")
            time.sleep(10)

    conn.close()
    print(f"Ano {year} concluído.")


if __name__ == "__main__":
    args = sys.argv[1:]
    redo = False
    if args and args[0] == "--redo":
        redo = True
        args = args[1:]
    if args:
        for y in args:
            process_year(int(y), redo=redo)
    else:
        print("Uso: python generate_explanations.py <ano1> <ano2> ...")
        print("Ex.: python generate_explanations.py 2022 2023 2024 2025 2026")
        print("Refazer um ano inteiro (sobrescreve, ex. com modelos grandes amanhã):")
        print("Ex.: python generate_explanations.py --redo 2026")
