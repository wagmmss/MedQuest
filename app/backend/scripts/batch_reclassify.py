"""
Motor de Recategorização Médica de Alta Acurácia - MedQuest
Classifica questões de Residência Médica em 5 Grandes Áreas e 170 Subtemas Canônicos.
Utiliza IA médica de ponta (Gemini 3.6 Flash / OpenRouter LLaMA-3.3-70B) com contexto clínico completo:
- Enunciado da questão (stem)
- Alternativas A-E completas
- Gabarito Oficial (correct_letter / is_correct)
- Comentário do Professor (explanations)
- Metadados de Origem (topic / subtema_orig)
"""

import argparse
import difflib
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Carregar chaves de API
def get_env_keys():
    keys = {}
    for p in [Path(".env"), Path("app/.env"), Path("app/backend/.env"), Path("../../.env")]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        keys[k.strip()] = v.strip().strip('"').strip("'")
    return keys

ENV_KEYS = get_env_keys()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ENV_KEYS.get("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or ENV_KEYS.get("OPENROUTER_API_KEY")

# Carregar Taxonomia Canônica
TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "taxonomy.json"
if not TAXONOMY_PATH.exists():
    TAXONOMY_PATH = Path("app/backend/data/taxonomy.json")

with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
    RAW_TAXONOMY = json.load(f)

CANONICAL_TAXONOMY = {}
for a in RAW_TAXONOMY:
    CANONICAL_TAXONOMY[a["area"]] = [m["theme"] for m in a["macroThemes"]]

VALID_AREAS = list(CANONICAL_TAXONOMY.keys())

def normalize_str(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()

def match_canonical_subtema(target_area: str, subtema_raw: str) -> str:
    """Garante que o subtema corresponda exatamente a um dos subtemas canônicos da área."""
    if not subtema_raw:
        return CANONICAL_TAXONOMY.get(target_area, ["Geral"])[0]

    # Normalizar área
    if target_area not in CANONICAL_TAXONOMY:
        norm_area = normalize_str(target_area)
        for valid_a in VALID_AREAS:
            if normalize_str(valid_a) == norm_area:
                target_area = valid_a
                break
        else:
            target_area = "Clínica Médica"

    available = CANONICAL_TAXONOMY[target_area]
    
    # 1. Match exato
    if subtema_raw in available:
        return subtema_raw
    
    # 2. Match normalizado (sem acento, case-insensitive)
    norm_target = normalize_str(subtema_raw)
    for s in available:
        if normalize_str(s) == norm_target:
            return s
            
    # 3. Match por substring
    for s in available:
        norm_s = normalize_str(s)
        if norm_target in norm_s or norm_s in norm_target:
            return s
            
    # 4. Fuzzy match na mesma área
    matches = difflib.get_close_matches(subtema_raw, available, n=1, cutoff=0.5)
    if matches:
        return matches[0]

    # 5. Se não encontrou na área, procurar em TODAS as outras áreas (caso o modelo tenha trocado a área)
    for other_a, subs in CANONICAL_TAXONOMY.items():
        for s in subs:
            if normalize_str(s) == norm_target or norm_target in normalize_str(s):
                return s
        matches_other = difflib.get_close_matches(subtema_raw, subs, n=1, cutoff=0.6)
        if matches_other:
            return matches_other[0]
        
    return available[0]


def init_audit_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reclassification_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            old_area TEXT,
            old_subtema TEXT,
            new_area TEXT NOT NULL,
            new_subtema TEXT NOT NULL,
            confidence REAL,
            rationale TEXT,
            model_used TEXT,
            applied INTEGER DEFAULT 0,
            classified_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_qid ON reclassification_audit(question_id)")
    conn.commit()


def call_gemini(prompt: str, model="gemini-3.6-flash", max_retries=5) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = 6 * (attempt + 1)
                print(f"   [Gemini 429] Aguardando {wait_time}s para liberar cota...")
                time.sleep(wait_time)
                continue
            if attempt == max_retries - 1:
                raise
            time.sleep(3)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(3)
    raise RuntimeError("Falha após retries no Gemini.")


DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or ENV_KEYS.get("DEEPSEEK_API_KEY")


def call_deepseek(prompt: str, model="deepseek-chat", max_retries=3) -> dict:
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY não configurada.")
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                if "```json" in content:
                    content = content.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in content:
                    content = content.split("```", 1)[1].split("```", 1)[0].strip()
                return json.loads(content)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(3)
    raise RuntimeError("Falha após retries no DeepSeek.")


def call_openrouter(prompt: str, model="meta-llama/llama-3.3-70b-instruct", max_retries=3) -> dict:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY não configurada.")
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://medquest.app",
        "X-Title": "MedQuest"
    }
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                if "```json" in content:
                    content = content.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in content:
                    content = content.split("```", 1)[1].split("```", 1)[0].strip()
                return json.loads(content)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
    raise RuntimeError("Falha após retries no OpenRouter.")


def classify_batch_ai(batch: list[dict], model_provider="deepseek", target_area_focus=None) -> list[dict]:
    """Envia lote para classificação médica estruturada com a taxonomia canônica completa de 170 subtemas."""
    tax_section = f"TAXONOMIA OFICIAL (5 GRANDES ÁREAS E 170 SUBTEMAS):\n{json.dumps(CANONICAL_TAXONOMY, ensure_ascii=False)}"

    system_instructions = f"""Médico Examinador Oficial de Residência Médica. Classifique cada questão em exatamente 1 Grande Área e 1 Subtema canônico.

{tax_section}

DIRETRIZES CLÍNICAS:
- 'a': uma das 5 áreas ('Cirurgia', 'Clínica Médica', 'Ginecologia e Obstetrícia', 'Pediatria', 'Medicina Preventiva').
- 's': string EXATA do subtema canônico pertencente à área escolhida.
- Avalie caso clínico, alternativas, gabarito e explicação médica.
- Trauma cirúrgico/procedimentos cirúrgicos→Cirurgia.
- DISTINÇÃO EM CIRURGIA:
  * 'Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)': trauma facial e cervical.
  * 'Fraturas Ósseas e Princípios Gerais de Osteossíntese': fraturas ósseas gerais, Gustilo, osteossíntese.
  * 'Trauma Ortopédico de Extremidades e Síndrome Compartimental': membros, partes moles, síndrome compartimental.
  * 'Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise': afecções ortopédicas pediátricas.
- Doenças/infecções na infância, neonatologia, puericultura→Pediatria.
- Gestação, parto, puerpério, distúrbios ginecológicos→Ginecologia e Obstetrícia.
- SUS, epidemiologia, bioestatística, saúde coletiva/trabalhador→Medicina Preventiva.
- Doenças clínicas do adulto não cirúrgico→Clínica Médica.

JSON: {{"r":[{{"id":<int>,"a":"<Área>","s":"<Subtema>","c":<0.0-1.0>,"j":"<justificativa clínica>"}}]}}"""

    items = []
    for q in batch:
        item = {"id": q["id"], "q": q["stem"]}
        if q["alts_formatted"]:
            item["alt"] = q["alts_formatted"]
        exp = (q["explanation"] or "")[:250]
        if exp:
            item["exp"] = exp
        items.append(item)

    user_text = json.dumps(items, ensure_ascii=False, separators=(',', ':'))
    full_prompt = system_instructions + "\n\n" + user_text

    for retry in range(5):
        try:
            if model_provider == "deepseek":
                response_json = call_deepseek(full_prompt, model="deepseek-chat")
                model_name = "deepseek-chat"
            elif model_provider == "gemini":
                response_json = call_gemini(full_prompt, model="gemini-3.6-flash")
                model_name = "gemini-3.6-flash"
            else:
                response_json = call_openrouter(full_prompt)
                model_name = "openrouter/llama-3.3-70b"
            break
        except Exception as e:
            wait = 10 * (retry + 1)
            print(f"   [Provedor {model_provider} falhou (tentativa {retry+1}/5)]: {e}. Aguardando {wait}s...")
            time.sleep(wait)
            if retry == 4:
                raise RuntimeError(f"Falha definitiva após 5 tentativas no provedor {model_provider}: {e}")

    raw_results = response_json.get("r") or response_json.get("results") or response_json.get("classifications") or []
    
    # Validação e saneamento dos resultados
    sanitized = []
    results_by_id = {r["id"]: r for r in raw_results if "id" in r}
    
    for q in batch:
        qid = q["id"]
        if qid in results_by_id:
            r = results_by_id[qid]
            raw_area = r.get("a") or r.get("target_area") or q["area"]
            target_area = raw_area if raw_area in VALID_AREAS else q["area"]
            if target_area not in VALID_AREAS:
                target_area = "Clínica Médica"
                
            raw_sub = r.get("s") or r.get("target_subtema") or q["subtema"]
            target_subtema = match_canonical_subtema(target_area, raw_sub)
            
            sanitized.append({
                "id": qid,
                "old_area": q["area"],
                "old_subtema": q["subtema"],
                "target_area": target_area,
                "target_subtema": target_subtema,
                "confidence": float(r.get("c") or r.get("confidence") or 0.95),
                "rationale": str(r.get("j") or r.get("rationale") or "").strip(),
                "model_used": model_name
            })
        else:
            sanitized.append({
                "id": qid,
                "old_area": q["area"],
                "old_subtema": q["subtema"],
                "target_area": q["area"],
                "target_subtema": q["subtema"],
                "confidence": 0.5,
                "rationale": "Não retornado no lote de IA (preservado original)",
                "model_used": "fallback"
            })
            
    return sanitized


def fetch_questions(conn: sqlite3.Connection, area=None, limit=None, offset=0, ids=None, skip_audited=False):
    conn.row_factory = sqlite3.Row
    query = """
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE 1=1
    """
    params = []
    if skip_audited:
        query += " AND q.id NOT IN (SELECT question_id FROM reclassification_audit)"
    if ids:
        placeholders = ",".join("?" for _ in ids)
        query += f" AND q.id IN ({placeholders})"
        params.extend(ids)
    elif area:
        query += " AND q.area = ?"
        params.append(area)
        
    query += " ORDER BY q.id"
    if limit is not None:
        query += f" LIMIT {limit} OFFSET {offset}"

    rows = conn.execute(query, params).fetchall()
    
    questions = []
    for r in rows:
        qid = r["id"]
        alts = conn.execute("SELECT letter, text, is_correct FROM alternatives WHERE question_id = ? ORDER BY letter", (qid,)).fetchall()
        alts_formatted = "\n".join([f"  {a['letter']}) {a['text']}" + (" [GABARITO OFICIAL]" if a['is_correct'] else "") for a in alts])
        
        questions.append({
            "id": qid,
            "stem": r["stem"] or "",
            "topic": r["topic"] or "",
            "subtema_orig": r["subtema_orig"] or "",
            "area": r["area"] or "",
            "subtema": r["subtema"] or "",
            "explanation": r["explanation_text"] or "",
            "alts_formatted": alts_formatted
        })
    return questions


def main():
    parser = argparse.ArgumentParser(description="Reclassificador de Questões do MedQuest")
    parser.add_argument("--db", default="app/backend/medquest.db", help="Caminho do medquest.db")
    parser.add_argument("--area", default=None, help="Filtrar por área atual")
    parser.add_argument("--batch-size", type=int, default=15, help="Tamanho do lote por requisição (recomendado: 15)")
    parser.add_argument("--limit", type=int, default=None, help="Limite total de questões a processar")
    parser.add_argument("--offset", type=int, default=0, help="Offset inicial")
    parser.add_argument("--ids", default=None, help="Lista de IDs separados por vírgula")
    parser.add_argument("--apply", action="store_true", help="Aplica as alterações no banco de dados")
    parser.add_argument("--skip-audited", action="store_true", help="Pula questões já auditadas/classificadas")
    parser.add_argument("--only-noncanonical", action="store_true", help="Classifica apenas questões cujo par área/subtema não pertence à taxonomia oficial")
    parser.add_argument("--out", default=None, help="Arquivo de saída do relatório Markdown")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "deepseek", "openrouter"], help="Provedor de IA")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=60.0)
    init_audit_table(conn)

    ids = [int(x.strip()) for x in args.ids.split(",")] if args.ids else None
    # Apply the canonical filter before the user-facing limit, otherwise an
    # initial block of already recovered questions can produce an empty run.
    fetch_limit = None if args.only_noncanonical else args.limit
    questions = fetch_questions(conn, area=args.area, limit=fetch_limit, offset=args.offset, ids=ids, skip_audited=args.skip_audited)
    if args.only_noncanonical:
        questions = [q for q in questions if q["area"] not in CANONICAL_TAXONOMY or q["subtema"] not in CANONICAL_TAXONOMY.get(q["area"], [])]
        if args.limit is not None:
            questions = questions[:args.limit]

    print(f"==================================================")
    print(f"INICIANDO RECATEGORIZAÇÃO MÉDICA - MEDQUEST")
    print(f"Total de questões selecionadas: {len(questions)}")
    print(f"Modo: {'APLICAÇÃO DIRETA NO BANCO' if args.apply else 'DRY-RUN (AUDITORIA/SIMULAÇÃO)'}")
    print(f"Tamanho do lote: {args.batch_size} | Provedor: {args.provider}")
    print(f"==================================================\n")

    if not questions:
        print("Nenhuma questão encontrada com os filtros especificados.")
        return

    all_results = []
    now_iso = datetime.now(timezone.utc).isoformat()

    total_batches = (len(questions) + args.batch_size - 1) // args.batch_size
    for b_idx in range(total_batches):
        batch = questions[b_idx * args.batch_size : (b_idx + 1) * args.batch_size]
        print(f"Processando Lote {b_idx + 1}/{total_batches} (Questões {batch[0]['id']} a {batch[-1]['id']})...")
        
        batch_results = classify_batch_ai(batch, model_provider=args.provider, target_area_focus=args.area)
        all_results.extend(batch_results)

        if args.apply:
            with conn:
                for res in batch_results:
                    conn.execute("""
                        INSERT INTO reclassification_audit 
                        (question_id, old_area, old_subtema, new_area, new_subtema, confidence, rationale, model_used, applied, classified_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (
                        res["id"], res["old_area"], res["old_subtema"],
                        res["target_area"], res["target_subtema"],
                        res["confidence"], res["rationale"], res["model_used"], now_iso
                    ))
                    conn.execute("""
                        UPDATE questions 
                        SET area = ?, 
                            subtema = ?,
                            subtema_orig = CASE WHEN subtema_orig IS NULL OR subtema_orig = '' THEN subtema ELSE subtema_orig END
                        WHERE id = ?
                    """, (res["target_area"], res["target_subtema"], res["id"]))
            print(f"   ✓ Lote {b_idx + 1} gravado com sucesso no banco!")
        else:
            print(f"   ✓ Lote {b_idx + 1} classificado com sucesso (modo simulação).")

        if b_idx < total_batches - 1:
            time.sleep(4.5 if args.provider == "gemini" else 2.0)

    area_changes = sum(1 for r in all_results if r["old_area"] != r["target_area"])
    subtema_changes = sum(1 for r in all_results if r["old_subtema"] != r["target_subtema"])
    avg_conf = sum(r["confidence"] for r in all_results) / len(all_results) if all_results else 0

    print(f"\n==================================================")
    print(f"RELATÓRIO RESUMIDO DO PROCESSAMENTO")
    print(f"Questões analisadas: {len(all_results)}")
    print(f"Mudanças de Grande Área: {area_changes} ({area_changes/len(all_results)*100:.1f}%)")
    print(f"Mudanças de Subtema: {subtema_changes} ({subtema_changes/len(all_results)*100:.1f}%)")
    print(f"Confiança Média: {avg_conf*100:.1f}%")
    print(f"==================================================")

    if args.out:
        out_path = Path(args.out)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# Relatório de Auditoria de Recategorização Médica\n\n")
            f.write(f"- Data: `{now_iso}`\n")
            f.write(f"- Total de Questões: `{len(all_results)}`\n")
            f.write(f"- Mudanças de Área: `{area_changes}`\n")
            f.write(f"- Mudanças de Subtema: `{subtema_changes}`\n")
            f.write(f"- Confiança Média: `{avg_conf*100:.1f}%`\n\n")
            f.write(f"| ID | Área Anterior | Subtema Anterior | Nova Área | Novo Subtema | Confiança | Justificativa Médica |\n")
            f.write(f"| :--- | :--- | :--- | :--- | :--- | :---: | :--- |\n")
            for r in all_results:
                f.write(f"| **{r['id']}** | {r['old_area']} | {r['old_subtema']} | **{r['target_area']}** | **{r['target_subtema']}** | {r['confidence']:.2f} | {r['rationale']} |\n")
        print(f"Relatório detalhado salvo em: {out_path}")

if __name__ == "__main__":
    main()
