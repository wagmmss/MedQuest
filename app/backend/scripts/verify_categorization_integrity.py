#!/usr/bin/env python3
"""
verify_categorization_integrity.py

Verifica a integridade completa das categorias das questões no banco MedQuest:
1. Valida se todas as questões possuem area, subtema e subtema_id preenchidos.
2. Valida se todo subtema pertence à taxonomia canônica oficial (canonical_taxonomy.json).
3. Valida se o subtema_id confere com o subtema_map.json.
4. Gera métricas de distribuição por Grande Área.
5. Valida integridade da tabela de auditoria (reclassification_audit).
"""

import os
import sys
import json
import sqlite3
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("MEDQUEST_DB", os.path.join(BACKEND_DIR, "medquest.db"))
CANONICAL_TAXONOMY_PATH = os.path.join(BACKEND_DIR, "data", "canonical_taxonomy.json")
SUBTEMA_MAP_PATH = os.path.join(BACKEND_DIR, "data", "subtema_map.json")


def main():
    print("=" * 80)
    print("MEDQUEST - VERIFICADOR DE INTEGRIDADE TAXONÔMICA E DE CATEGORIAS")
    print(f"Database: {DB_PATH}")
    print("=" * 80)

    with open(CANONICAL_TAXONOMY_PATH, "r", encoding="utf-8") as f:
        canonical_taxonomy = json.load(f)

    with open(SUBTEMA_MAP_PATH, "r", encoding="utf-8") as f:
        subtema_map = json.load(f)

    canonical_areas = set(canonical_taxonomy.keys())
    canonical_subtemas_by_area = {k: set(v.keys()) for k, v in canonical_taxonomy.items()}
    all_canonical_subtemas = set(subtema_map.keys())

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM questions")
    total_questions = cur.fetchone()[0]

    cur.execute("SELECT id, area, subtema, subtema_id, topic, institution_code, year, source_number FROM questions")
    rows = [dict(r) for r in cur.fetchall()]

    errors = []
    warnings = []

    area_counts = Counter()
    subtema_counts = Counter()

    for r in rows:
        qid = r["id"]
        area = r.get("area")
        subtema = r.get("subtema")
        sub_id = r.get("subtema_id")

        # 1. Null / empty check
        if not area:
            errors.append(f"Q#{qid} ({r['institution_code']} {r['year']}): 'area' está vazia/nula.")
        if not subtema:
            errors.append(f"Q#{qid} ({r['institution_code']} {r['year']}): 'subtema' está vazio/nulo.")
        if not sub_id:
            warnings.append(f"Q#{qid} ({r['institution_code']} {r['year']}): 'subtema_id' está vazio.")

        # 2. Canonical Area check
        if area and area not in canonical_areas:
            errors.append(f"Q#{qid}: Área '{area}' não é uma área canônica.")

        # 3. Canonical Subtema check
        if subtema:
            if subtema not in all_canonical_subtemas:
                errors.append(f"Q#{qid}: Subtema '{subtema}' não existe na taxonomia canônica.")
            elif area and area in canonical_subtemas_by_area:
                if subtema not in canonical_subtemas_by_area[area]:
                    warnings.append(f"Q#{qid}: Subtema '{subtema}' pertence a outra área canônica que não '{area}'.")

        # 4. Subtema ID match check
        if subtema and sub_id:
            expected_id = subtema_map.get(subtema)
            if expected_id and sub_id != expected_id:
                warnings.append(f"Q#{qid}: subtema_id '{sub_id}' diverge do esperado '{expected_id}' para '{subtema}'.")

        area_counts[area] += 1
        subtema_counts[(area, subtema)] += 1

    # Check audit table
    cur.execute("SELECT COUNT(*) FROM reclassification_audit")
    audit_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reclassification_audit WHERE model_used = 'medway_trilhas_confrontation'")
    medway_audit_count = cur.fetchone()[0]

    conn.close()

    print(f"\nTotal de Questões Verificadas: {total_questions}")
    print(f"Total de Registros de Auditoria: {audit_count} (Confrontação Medway: {medway_audit_count})")

    print("\n--- Distribuição por Grande Área ---")
    for area, cnt in sorted(area_counts.items(), key=lambda x: str(x[0])):
        pct = (cnt / total_questions) * 100 if total_questions else 0
        print(f"  {area or '*(Vazio)*'}: {cnt} questões ({pct:.1f}%)")

    print(f"\nTotal de Subtemas Distintos Ativos no Banco: {len(subtema_counts)} / 170 canônicos")

    print("\n--- Status de Conformidade ---")
    if errors:
        print(f"❌ [ERRO] Foram encontrados {len(errors)} erros de conformidade:")
        for err in errors[:20]:
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  ... e mais {len(errors) - 20} erros.")
        sys.exit(1)
    else:
        print("✅ [SUCESSO] 0 Erros de integridade! Todas as áreas e subtemas são válidos.")

    if warnings:
        print(f"⚠️ [AVISO] {len(warnings)} avisos/divergências secundárias identificadas:")
        for w in warnings[:10]:
            print(f"  - {w}")
        if len(warnings) > 10:
            print(f"  ... e mais {len(warnings) - 10} avisos.")
    else:
        print("✅ 0 Avisos. Integridade 100% perfeita!")


if __name__ == "__main__":
    main()
