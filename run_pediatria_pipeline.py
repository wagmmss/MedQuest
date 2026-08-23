import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pediatria_classifier_engine import classify_ped_item, TAX_170

DB_PATH = "app/backend/medquest.db"

def get_pending_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE id NOT IN (SELECT question_id FROM reclassification_audit)
        AND area = 'Pediatria'
    """)
    return c.fetchone()[0]

def process_batch(batch_size=100, batch_num=1):
    out_file = f"ped_b_next.json"
    cmd_dump = [
        "uv", "run", "python", "app/backend/scripts/dump_batch.py",
        "--area", "Pediatria",
        "--limit", str(batch_size),
        "--offset", "0",
        "--out", out_file
    ]
    res = subprocess.run(cmd_dump, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"Erro no dump: {res.stderr}")
        return 0

    if not Path(out_file).exists():
        print("Arquivo de saída não encontrado.")
        return 0

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("Nenhuma questão pendente no lote.")
        return 0

    print(f"\n--- Processando Lote {batch_num} ({len(data)} questões) ---")

    classifications = []
    for q in data:
        area, subtema, rationale = classify_ped_item(q)
        # Validar rigorosamente
        if area not in TAX_170 or subtema not in TAX_170[area]:
            print(f"ERRO: Classificação inválida para ID {q['id']}: {area} -> {subtema}")
            sys.exit(1)
        
        classifications.append({
            "id": q["id"],
            "target_area": area,
            "target_subtema": subtema,
            "confidence": 1.0,
            "rationale": rationale
        })

    class_file = "ped_b_next_classified.json"
    with open(class_file, "w", encoding="utf-8") as f:
        json.dump(classifications, f, ensure_ascii=False, indent=2)

    cmd_apply = [
        "uv", "run", "python", "app/backend/scripts/apply_agent_batch.py",
        class_file
    ]
    res_apply = subprocess.run(cmd_apply, capture_output=True, text=True, encoding="utf-8")
    if res_apply.returncode != 0:
        print(f"Erro ao aplicar: {res_apply.stderr}")
        sys.exit(1)

    print(res_apply.stdout.strip())
    return len(data)

def main():
    batch_num = 1
    total_processed = 0
    while True:
        pending = get_pending_count()
        print(f"Pendentes em Pediatria: {pending}")
        if pending == 0:
            print("Todas as questões de Pediatria foram processadas e auditadas com sucesso!")
            break
        
        count = process_batch(batch_size=100, batch_num=batch_num)
        if count == 0:
            break
        total_processed += count
        batch_num += 1

    print(f"\nTotal geral processado nesta execução: {total_processed} questões.")

if __name__ == "__main__":
    main()
