"""
Reclassifica TODAS as questões (área + subtema) usando a taxonomia canônica v2.
Diferenças em relação ao reclassify_subtemas.py original:
  - Reclassifica TODAS as questões, não apenas as não-canônicas
  - Classifica ÁREA e SUBTEMA juntos (corrige questões na área errada)
  - Prompt muito mais detalhado com instruções anti-erro
  - Usa stem completo (até 500 chars) ao invés de 220
  - Validação pós-classificação
  - Logging detalhado
  - Backup automático antes de aplicar

Uso:
    python reclassify_all.py              # reclassifica tudo (dry-run por padrão)
    python reclassify_all.py --apply      # aplica as mudanças no banco
    python reclassify_all.py --area "Cirurgia"  # apenas uma área
"""
import difflib
import json
import os
import shutil
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime

from canonical_subtemas import CANONICAL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reclass_v2.log")

api_key = os.environ.get("GEMINI_API_KEY", "")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
HEADERS = {
    "Content-Type": "application/json",
}
BATCH_SIZE = 40
SLEEP_BETWEEN = 2

# Pré-computa lista de áreas e subtemas por área
ALL_AREAS = list(CANONICAL.keys())
AREA_SUBTEMAS = {}
for area, subs in CANONICAL.items():
    AREA_SUBTEMAS[area] = {s.casefold().strip(): s for s in subs}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def call_gemini_json(prompt, max_attempts=50):
    for _ in range(max_attempts):
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0
            }
        }).encode("utf-8")
        try:
            req = urllib.request.Request(GEMINI_URL, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(content)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                log("    rate-limit, aguardando 15s...")
                time.sleep(15)
                continue
            if 500 <= e.code < 600:
                time.sleep(10)
                continue
            log(f"    ERRO HTTP {e.code}: {e.read().decode('utf-8')[:200]}")
            raise
    raise RuntimeError("Muitas tentativas seguidas de limite.")


def build_matcher(canon_list):
    """Mapeia rótulo da IA → rótulo canônico exato."""
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


def build_area_matcher():
    norm = {a.casefold().strip(): a for a in ALL_AREAS}
    def match(label):
        if not label:
            return None
        key = label.casefold().strip()
        if key in norm:
            return norm[key]
        close = difflib.get_close_matches(key, list(norm.keys()), n=1, cutoff=0.6)
        return norm[close[0]] if close else None
    return match


def build_prompt(batch_questions):
    """Constrói o prompt de classificação com todas as áreas e subtemas."""
    
    # Lista todas as áreas e subtemas
    taxonomy_text = ""
    for area in ALL_AREAS:
        subs = CANONICAL[area]
        numbered = "\n".join(f"    {i+1}. {s}" for i, s in enumerate(subs))
        taxonomy_text += f"\n  ÁREA: {area}\n  Subtemas:\n{numbered}\n"
    
    # Lista as questões
    qlist = ""
    for q in batch_questions:
        stem_clean = q["stem"][:500].strip().replace("\n", " ")
        qlist += f'- id {q["id"]}: {stem_clean}\n'
    
    prompt = f"""Você é um especialista em classificar questões de provas de residência médica.

TAXONOMIA COMPLETA (use EXATAMENTE os nomes listados):
{taxonomy_text}

REGRAS OBRIGATÓRIAS:
1. Cada questão deve ser classificada em UMA área e UM subtema.
2. Use EXATAMENTE o nome da área e do subtema como listados acima.
3. Leia o enunciado INTEIRO. Classifique pelo TEMA PRINCIPAL da questão, não por palavras isoladas.
4. Uma questão sobre hipertensão arterial com diagnóstico e tratamento vai em "Clínica Médica" → "Hipertensão Arterial Sistêmica".
5. Uma questão sobre HAS em criança (pressão arterial pediátrica) vai em "Pediatria" → (subtema apropriado).
6. Questões sobre atendimento em UBS/ESF, SUS, epidemiologia, ética médica vão em "Medicina Preventiva e Social".
7. Questões sobre gestação, parto, puerpério, ginecologia vão em "Ginecologia e Obstetrícia".
8. Questões sobre trauma vão em "Cirurgia" APENAS se envolvem mecanismo traumático (acidente, queda, FAB, FAF).
9. Questões sobre doenças clínicas em adultos (ICC, IAM, AVC, diabetes, infecções) vão em "Clínica Médica".
10. Questões sobre doenças em crianças/lactentes/neonatos vão em "Pediatria", EXCETO cirurgia pediátrica.
11. NÃO classifique questões como "Trauma Torácico" se não há mecanismo traumático — use o subtema adequado.
12. NÃO confunda "cirurgia" com doenças clínicas que podem ser operadas. Ex: nódulo de tireoide investigado clinicamente = Clínica Médica.

Responda APENAS em JSON:
{{"results": [{{"id": <numero>, "area": "<área>", "subtema": "<subtema>"}}]}}

QUESTÕES A CLASSIFICAR:
{qlist}"""
    
    return prompt


def backup_db():
    """Faz backup do banco antes de aplicar mudanças."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH + f".bak-before-reclass-v2-{ts}"
    shutil.copy2(DB_PATH, backup_path)
    log(f"Backup criado: {backup_path}")
    return backup_path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplica mudanças no banco (default: dry-run)")
    parser.add_argument("--area", type=str, help="Reclassifica apenas uma área específica")
    parser.add_argument("--offset", type=int, default=0, help="Pular N questões (para retomar)")
    args = parser.parse_args()

    # Limpa log
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"=== Reclassificação v2 - {datetime.now().isoformat()} ===\n")
        f.write(f"Modo: {'APPLY' if args.apply else 'DRY-RUN'}\n\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.apply:
        backup_db()

    # Seleciona questões para reclassificar
    if args.area:
        questions = conn.execute(
            "SELECT id, stem, area, subtema FROM questions WHERE area = ? AND missing_alts = 0 ORDER BY id",
            (args.area,)
        ).fetchall()
    else:
        questions = conn.execute(
            "SELECT id, stem, area, subtema FROM questions WHERE missing_alts = 0 AND area IS NOT NULL ORDER BY id"
        ).fetchall()

    questions = [dict(q) for q in questions]
    total = len(questions)
    log(f"Total de questões para reclassificar: {total}")

    if args.offset > 0:
        questions = questions[args.offset:]
        log(f"Pulando {args.offset} questões (offset), restam {len(questions)}")

    area_match = build_area_matcher()
    sub_matchers = {area: build_matcher(subs) for area, subs in CANONICAL.items()}
    
    # Resultados acumulados
    results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reclass_v2_results.jsonl")
    
    changed = 0
    skipped = 0
    errors = 0
    
    for start in range(0, len(questions), BATCH_SIZE):
        batch = questions[start:start + BATCH_SIZE]
        batch_num = (args.offset + start) // BATCH_SIZE + 1
        
        prompt = build_prompt(batch)
        
        try:
            data = call_gemini_json(prompt)
            results = {}
            for r in data.get("results", []):
                results[int(r["id"])] = {
                    "area": r.get("area", ""),
                    "subtema": r.get("subtema", "")
                }
        except Exception as e:
            log(f"  ERRO no lote {batch_num}: {e}")
            errors += len(batch)
            time.sleep(10)
            continue

        for q in batch:
            qid = q["id"]
            result = results.get(qid, {})
            
            new_area_raw = result.get("area", "")
            new_sub_raw = result.get("subtema", "")
            
            new_area = area_match(new_area_raw)
            if not new_area:
                log(f"    ID {qid}: área não reconhecida '{new_area_raw}' → mantida")
                skipped += 1
                continue
            
            matcher = sub_matchers.get(new_area)
            if not matcher:
                skipped += 1
                continue
            
            new_sub = matcher(new_sub_raw)
            if not new_sub:
                log(f"    ID {qid}: subtema não reconhecido '{new_sub_raw}' em {new_area} → mantido")
                skipped += 1
                continue
            
            old_area = q["area"]
            old_sub = q["subtema"]
            
            if old_area != new_area or old_sub != new_sub:
                changed += 1
                # Salva resultado
                with open(results_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "id": qid,
                        "old_area": old_area, "old_subtema": old_sub,
                        "new_area": new_area, "new_subtema": new_sub,
                        "stem_preview": q["stem"][:150]
                    }, ensure_ascii=False) + "\n")
                
                if args.apply:
                    conn.execute(
                        "UPDATE questions SET area = ?, subtema = ? WHERE id = ?",
                        (new_area, new_sub, qid)
                    )
        
        if args.apply:
            conn.commit()
        
        processed = args.offset + start + len(batch)
        log(f"  Lote {batch_num}: {changed} mudanças, {skipped} sem match, {errors} erros | {processed}/{total} ({100*processed/total:.1f}%)")
        time.sleep(SLEEP_BETWEEN)
    
    conn.close()
    
    log("\n=== CONCLUÍDO ===")
    log(f"Total processado: {total}")
    log(f"Mudanças: {changed}")
    log(f"Sem match: {skipped}")
    log(f"Erros: {errors}")
    log(f"Resultados em: {results_file}")
    if not args.apply:
        log("MODO DRY-RUN: nenhuma mudança foi aplicada no banco.")
        log("Para aplicar, execute com --apply")


if __name__ == "__main__":
    main()
