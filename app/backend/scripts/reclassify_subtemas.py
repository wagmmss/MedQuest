# -*- coding: utf-8 -*-
"""
Reclassifica os subtemas fragmentados em uma taxonomia canônica (canonical_subtemas.py),
usando o Groq em lotes. Seguro e reversível:
  - Cria a coluna `subtema_orig` guardando o subtema original (backup no próprio banco).
  - Só mexe em questões cujo subtema ainda NÃO é canônico (idempotente / resumível).

Uso:
    python reclassify_subtemas.py            # todas as áreas
    python reclassify_subtemas.py "Cirurgia" # uma área específica
"""
import os
import sys
import json
import time
import difflib
import sqlite3
import urllib.request
import urllib.error

from canonical_subtemas import CANONICAL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

# ── Chave Groq (.env em ../../) ────────────────────────────────────
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
    print("GROQ_API_KEY não encontrada no .env!")
    sys.exit(1)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Rotação de modelos (cada um tem cota diária separada). Para classificar categorias,
# até os menores vão bem — então a ordem prioriza cota alta/velocidade.
MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]
_model_idx = 0
HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}
BATCH_SIZE = 10
SLEEP_BETWEEN = 8   # segundos entre lotes (respeita ~12k tokens/min)


def call_groq_json(prompt, max_attempts=50):
    global _model_idx
    for _ in range(max_attempts):
        if _model_idx >= len(MODELS):
            raise RuntimeError("Todos os modelos esgotaram a cota diária. Tente amanhã.")
        model = MODELS[_model_idx]
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode("utf-8")
        try:
            req = urllib.request.Request(GROQ_URL, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return json.loads(data["choices"][0]["message"]["content"])
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
                if "per day" in msg or "tpd" in msg or wait > 120:
                    print(f"    modelo {model} esgotou a cota diária — trocando de modelo.")
                    _model_idx += 1
                    continue
                print(f"    limite por minuto em {model}, aguardando {wait:.0f}s...")
                time.sleep(wait + 1)
                continue
            if 500 <= e.code < 600:
                time.sleep(10)
                continue
            raise
    raise RuntimeError("Muitas tentativas seguidas de limite.")


def ensure_backup_column(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(questions)")]
    if "subtema_orig" not in cols:
        conn.execute("ALTER TABLE questions ADD COLUMN subtema_orig TEXT")
    # Guarda o original apenas onde ainda não foi guardado
    conn.execute("UPDATE questions SET subtema_orig = subtema WHERE subtema_orig IS NULL")
    conn.commit()


def build_matcher(canon_list):
    """Devolve função que mapeia um rótulo devolvido pela IA -> rótulo canônico exato."""
    norm = {c.casefold().strip(): c for c in canon_list}
    def match(label):
        if not label:
            return None
        key = label.casefold().strip()
        if key in norm:
            return norm[key]
        close = difflib.get_close_matches(key, list(norm.keys()), n=1, cutoff=0.6)
        return norm[close[0]] if close else None
    return match


def process_area(conn, area):
    canon = CANONICAL.get(area)
    if not canon:
        print(f"[pulando] área sem taxonomia: {area}")
        return
    match = build_matcher(canon)
    canon_set = set(canon)

    cur = conn.cursor()
    cur.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(canon))
    todo = cur.execute(
        f"""SELECT id, stem, subtema FROM questions
            WHERE area = ? AND missing_alts = 0
              AND subtema IS NOT NULL AND subtema != ''
              AND subtema NOT IN ({placeholders})
            ORDER BY id""",
        (area, *canon),
    ).fetchall()

    print(f"\n===== {area}: {len(todo)} questões para reclassificar =====")
    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(canon))

    changed = skipped = 0
    for start in range(0, len(todo), BATCH_SIZE):
        batch = todo[start:start + BATCH_SIZE]
        qlist = "\n".join(
            f'- id {q["id"]}: (atual: {q["subtema"]}) {q["stem"][:220].strip()}'
            for q in batch
        )
        prompt = f"""Você classifica questões médicas de {area} em UMA categoria de uma lista fixa.

CATEGORIAS PERMITIDAS (use EXATAMENTE este texto):
{numbered}

Para cada questão abaixo, escolha a categoria mais adequada da lista. Se nenhuma encaixar perfeitamente, escolha a mais próxima. Responda em JSON no formato:
{{"results": [{{"id": <numero>, "subtema": "<texto exato de uma categoria>"}}]}}

QUESTÕES:
{qlist}"""

        try:
            data = call_groq_json(prompt)
            results = {int(r["id"]): r.get("subtema") for r in data.get("results", [])}
        except Exception as e:
            print(f"    erro no lote {start}-{start+len(batch)}: {e}")
            time.sleep(10)
            continue

        for q in batch:
            canonical = match(results.get(q["id"]))
            if canonical and canonical in canon_set:
                conn.execute("UPDATE questions SET subtema = ? WHERE id = ?", (canonical, q["id"]))
                changed += 1
            else:
                skipped += 1
        conn.commit()
        print(f"  lote {start//BATCH_SIZE + 1}: {changed} classificadas, {skipped} sem match até agora")
        time.sleep(SLEEP_BETWEEN)

    print(f"{area} concluída: {changed} reclassificadas, {skipped} sem match (mantidas como estavam).")


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_backup_column(conn)
    areas = sys.argv[1:] if len(sys.argv) > 1 else list(CANONICAL.keys())
    for area in areas:
        process_area(conn, area)
    conn.close()
    print("\nPronto. (Para desfazer: UPDATE questions SET subtema = subtema_orig;)")


if __name__ == "__main__":
    main()
