#!/usr/bin/env python3
"""Audita, sem alterar o banco, categorias das questões contra os HARs Medway.

Uma proposta é ``eligible_for_apply`` apenas quando há uma questão Medway única
com o mesmo enunciado normalizado e uma tag Medway com mapeamento canônico único.
Os demais casos permanecem explicitamente em fila de revisão; este programa nunca
usa similaridade textual ou metadados isolados para sugerir alteração automática.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_DB = BACKEND / "medquest.db"
DEFAULT_HARS = Path(r"C:\Users\wmors\Downloads\Medway_Trilhas")
DEFAULT_REPORT = BACKEND.parent.parent / "docs" / "audits" / "medway-trilhas-har-dry-run.json"


def normalize(value: str | None) -> str:
    """Normaliza texto sem apagar conteúdo clínico nem aceitar aproximações."""
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokens(value: str | None) -> list[str]:
    """Tokens comparáveis; ignora imagens e marcação que não existem nos HARs."""
    value = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char)).lower()
    return re.findall(r"[a-z0-9]{2,}", value)


def load_taxonomy() -> tuple[dict[str, tuple[str, str]], set[tuple[str, str]]]:
    """Returns aliases from the curated de-para and the allowed canonical pairs."""
    canonical = json.loads((BACKEND / "data" / "canonical_taxonomy.json").read_text(encoding="utf-8"))
    valid_pairs = {(area, subtema) for area, subtemas in canonical.items() for subtema in subtemas}
    aliases: dict[str, tuple[str, str]] = {}

    # Nomes que existem em mais de uma área não podem ser inferidos pelo nome
    # sozinho. Eles só entram pelo de-para (que declara a área) ou por uma
    # exceção explicitamente curada abaixo.
    pairs_by_subtema: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for area, subtema in valid_pairs:
        pairs_by_subtema[subtema].append((area, subtema))
    for subtema, pairs in pairs_by_subtema.items():
        if len(pairs) == 1:
            aliases[normalize(subtema)] = pairs[0]

    de_para = json.loads((BACKEND / "data" / "de_para_temas.json").read_text(encoding="utf-8"))
    for items in de_para.get("areas", {}).values():
        for item in items:
            target = item["nome_novo"]
            candidates = [pair for pair in valid_pairs if pair == (item["area"], target)]
            if len(candidates) == 1:
                aliases[normalize(item["nome_original"])] = candidates[0]

    # Variações presentes nos HARs que possuem correspondência canônica inequívoca.
    curated = {
        "Abdome Agudo Perfurativo": ("Cirurgia", "Abdome Agudo Perfurativo e Úlcera Péptica Perfurada"),
        "Abdome Agudo Isquêmico": ("Cirurgia", "Abdome Agudo Vascular e Isquemia Mesentérica"),
        "Abordagem Inicial (xABCDE)": ("Cirurgia", "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)"),
        "Afecções Benignas das Vias Biliares": ("Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite"),
        "Afecções Urológicas Benignas": ("Clínica Médica", "Hiperplasia Prostática Benigna (HPB) e Litíase Urinária"),
        "Cólon e Reto na cirurgia": ("Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais"),
        "Cuidados e Complicações pós-operatórias": ("Cirurgia", "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas"),
        "Cuidados Pré-operatórios": ("Cirurgia", "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico"),
        "Doenças Sexualmente transmissíveis": ("Clínica Médica", "Infecções Sexualmente Transmissíveis (ISTs) no Adulto"),
        "Doença arterial periférica": ("Cirurgia", "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas"),
        "Epilepsias e Crises Convulsivas": ("Pediatria", "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância"),
        "Estenose de Carótidas": ("Cirurgia", "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas"),
        "Fraturas ósseas": ("Cirurgia", "Fraturas Ósseas e Princípios Gerais de Osteossíntese"),
        "Hemorragia Digestiva (Cirurgia)": ("Cirurgia", "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica"),
        "HIV e AIDS no adulto não-gestante": ("Clínica Médica", "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas"),
        "Infecções Fúngicas": ("Clínica Médica", "Dermatoses Infecciosas, Hanseníase e Leishmanioses"),
        "Rotura Prematura das Membranas Ovulares e Infecção Ovular": ("Ginecologia e Obstetrícia", "Amniorrexe Prematura (RPMO) e Corioamnionite"),
        "Síndrome Disfágica": ("Cirurgia", "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica"),
        "Síndromes Dispépticas": ("Cirurgia", "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica"),
        "Síndromes hipertensivas na gestação": ("Ginecologia e Obstetrícia", "Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)"),
        "Tendinites/ Tenossinovites/ Fasceítes e Bursites": ("Cirurgia", "Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética"),
        "Trauma de face e pescoço": ("Cirurgia", "Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)"),
        "Trauma de membros e extremidades": ("Cirurgia", "Trauma Ortopédico de Extremidades e Síndrome Compartimental"),
        "Trauma Abdominal": ("Cirurgia", "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)"),
        "Trauma Torácico": ("Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco"),
        "Tumores Dermatológicos": ("Cirurgia", "Oncologia Cutânea: Melanoma, CBC e CEC"),
        "Tumores do Aparelho Digestivo": ("Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)"),
        "Tumores cabeça e Pescoço": ("Cirurgia", "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos"),
        "Tumores Pulmonares e do Mediastino": ("Cirurgia", "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino"),
    }
    for source, target in curated.items():
        if target not in valid_pairs:
            raise RuntimeError(f"Destino canônico inválido: {target}")
        aliases[normalize(source)] = target
    return aliases, valid_pairs


def extract_questions(hars_dir: Path) -> tuple[dict[int, dict[str, Any]], list[dict[str, str]]]:
    """Extracts only question endpoint payloads and records conflicting HAR copies."""
    questions: dict[int, dict[str, Any]] = {}
    conflicts: list[dict[str, str]] = []
    for har_path in sorted(hars_dir.glob("*.har")):
        har = json.loads(har_path.read_text(encoding="utf-8", errors="replace"))
        for entry in har.get("log", {}).get("entries", []):
            url = entry.get("request", {}).get("url", "")
            if "/api/v3/questions/" not in url or "/text-explanation/" in url:
                continue
            text = entry.get("response", {}).get("content", {}).get("text", "") or ""
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict) or not payload.get("id") or not payload.get("content"):
                continue
            tags = [tag.get("name", "") for tag in payload.get("tag", []) if isinstance(tag, dict) and tag.get("name")]
            record = {
                "medway_id": payload["id"], "stem": payload["content"], "stem_key": normalize(payload["content"]),
                "tags": sorted(set(tags)), "institution": (payload.get("institution") or {}).get("name"),
                "year": payload.get("year"), "original_number": payload.get("original_question_number"),
                "har_files": [har_path.name],
            }
            previous = questions.get(payload["id"])
            if previous is None:
                questions[payload["id"]] = record
            elif previous["stem_key"] == record["stem_key"] and previous["tags"] == record["tags"]:
                previous["har_files"].append(har_path.name)
            else:
                conflicts.append({"medway_id": str(payload["id"]), "first_har": previous["har_files"][0], "conflicting_har": har_path.name})
    return questions, conflicts


def classify_tag(tags: list[str], aliases: dict[str, tuple[str, str]]) -> tuple[tuple[str, str] | None, str]:
    destinations = {aliases[normalize(tag)] for tag in tags if normalize(tag) in aliases}
    if not tags:
        return None, "no_medway_tag"
    if not destinations:
        return None, "unmapped_medway_tag"
    if len(destinations) != 1:
        return None, "multiple_canonical_destinations"
    return destinations.pop(), "mapped"


def build_content_index(medway: dict[int, dict[str, Any]]) -> dict[tuple[str, ...], set[int]]:
    """Indexa sequências de oito palavras: evidência textual, não similaridade vaga."""
    index: dict[tuple[str, ...], set[int]] = defaultdict(set)
    for item in medway.values():
        item_tokens = tokens(item["stem"])
        for offset in range(len(item_tokens) - 7):
            index[tuple(item_tokens[offset : offset + 8])].add(item["medway_id"])
    return index


def content_match(stem: str | None, index: dict[tuple[str, ...], set[int]]) -> tuple[int | None, int, list[int]]:
    """Retorna candidato somente quando ao menos quatro trechos são exclusivos.

    Quatro sequências distintas de oito palavras consecutivas equivalem a pelo
    menos onze palavras contínuas em comum, mas toleram cabeçalho/imagens
    inseridos no banco. Casos menores ficam no relatório, nunca são aplicáveis.
    """
    votes: Counter[int] = Counter()
    item_tokens = tokens(stem)
    for offset in range(len(item_tokens) - 7):
        for medway_id in index.get(tuple(item_tokens[offset : offset + 8]), set()):
            votes[medway_id] += 1
    if not votes:
        return None, 0, []
    highest = max(votes.values())
    winners = sorted(key for key, value in votes.items() if value == highest)
    return (winners[0] if highest >= 4 and len(winners) == 1 else None), highest, winners[:10]


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run auditável: MedQuest x Medway Trilhas HAR")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--hars-dir", type=Path, default=DEFAULT_HARS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true", help="Aplica somente propostas com enunciado normalizado idêntico.")
    parser.add_argument(
        "--apply-content-matches",
        action="store_true",
        help=("Aplica correspondências com candidato único e quatro ou mais sequências "
              "exclusivas de oito palavras; use apenas após a revisão editorial do relatório."),
    )
    parser.add_argument("--batch-size", type=int, default=20, help="Máximo de alterações por execução (padrão: 20).")
    args = parser.parse_args()
    if args.apply and args.apply_content_matches:
        raise SystemExit("Escolha apenas uma modalidade de aplicação.")
    if args.batch_size < 1:
        raise SystemExit("--batch-size deve ser maior que zero.")
    if not args.db.is_file() or not args.hars_dir.is_dir():
        raise SystemExit("Banco ou diretório de HARs não encontrado.")

    aliases, valid_pairs = load_taxonomy()
    medway, har_conflicts = extract_questions(args.hars_dir)
    by_stem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in medway.values():
        by_stem[item["stem_key"]].append(item)
    content_index = build_content_index(medway)

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    db_rows = [dict(row) for row in db.execute("SELECT id, source_file, source_number, year, institution_code, area, subtema, subtema_id, topic, stem FROM questions ORDER BY id")]
    db.close()

    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for row in db_rows:
        candidates = by_stem.get(normalize(row["stem"]), [])
        base = {"question_id": row["id"], "current": {key: row[key] for key in ("area", "subtema", "subtema_id", "topic")}}
        match_method = "exact_normalized_stem"
        match_score = None
        if len(candidates) != 1:
            candidate_id, match_score, top_ids = content_match(row["stem"], content_index)
            if candidate_id is not None:
                candidates = [medway[candidate_id]]
                match_method = "four_or_more_unique_8_word_sequences"
            else:
                status = "unmatched" if match_score == 0 else "needs_content_review"
                records.append({**base, "status": status, "candidate_medway_ids": top_ids, "shared_8_word_sequences": match_score})
                counts[status] += 1
                continue
        if len(candidates) != 1:
            status = "unmatched" if not candidates else "ambiguous_medway_match"
            records.append({**base, "status": status, "candidate_medway_ids": [item["medway_id"] for item in candidates]})
            counts[status] += 1
            continue
        item = candidates[0]
        target, tag_status = classify_tag(item["tags"], aliases)
        evidence = {"medway_id": item["medway_id"], "har_files": item["har_files"], "tags": item["tags"], "match": match_method, "shared_8_word_sequences": match_score}
        if target is None:
            records.append({**base, "status": tag_status, "evidence": evidence})
            counts[tag_status] += 1
            continue
        target_area, target_subtema = target
        if (row["area"], row["subtema"]) == target:
            status = "already_aligned"
        elif match_method == "exact_normalized_stem":
            status = "eligible_for_apply"
        else:
            # A correspondência é forte, mas não é identidade textual integral;
            # requer conferência editorial antes de qualquer escrita.
            status = "proposed_content_match"
        records.append({**base, "status": status, "target": {"area": target_area, "subtema": target_subtema}, "evidence": evidence})
        counts[status] += 1

    input_hash = hashlib.sha256(args.db.read_bytes()).hexdigest()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "mode": "dry_run_no_database_changes",
        "database": str(args.db), "hars_dir": str(args.hars_dir), "har_files": len(list(args.hars_dir.glob("*.har"))),
        "medway_questions_unique": len(medway), "medway_duplicate_conflicts": har_conflicts,
        "database_questions": len(db_rows), "status_counts": dict(sorted(counts.items())),
        "taxonomy_pairs": len(valid_pairs), "records": records,
        "input_sha256": input_hash,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("database_questions", "har_files", "medway_questions_unique", "status_counts")}, ensure_ascii=False, indent=2))
    print(f"Relatório: {args.report}")

    if args.apply or args.apply_content_matches:
        applicable_statuses = {"eligible_for_apply"}
        model_used = "medway_trilhas_har_exact"
        match_label = "correspondência exata do enunciado"
        if args.apply_content_matches:
            applicable_statuses.add("proposed_content_match")
            model_used = "medway_trilhas_har_content_verified"
            match_label = "candidato único confirmado por quatro ou mais sequências exclusivas de oito palavras"
        changes = [record for record in records if record["status"] in applicable_statuses]
        if not changes:
            print("Nenhuma proposta elegível para aplicar.")
            return 0
        changes = sorted(changes, key=lambda record: record["question_id"])[:args.batch_size]
        if hashlib.sha256(args.db.read_bytes()).hexdigest() != input_hash:
            raise SystemExit("O banco mudou durante o dry-run; aplicação cancelada.")

        # Snapshot consistente pelo mecanismo SQLite, antes da transação de escrita.
        backup_dir = BACKEND.parent.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = backup_dir / f"medquest_{stamp}_pre-medway-har.db"
        source = sqlite3.connect(args.db)
        destination = sqlite3.connect(backup)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        subtema_ids = json.loads((BACKEND / "data" / "subtema_map.json").read_text(encoding="utf-8"))
        run_id = f"medway_har_{stamp}"
        db = sqlite3.connect(args.db)
        try:
            db.execute("BEGIN IMMEDIATE")
            for record in changes:
                old = record["current"]
                target = record["target"]
                current = db.execute("SELECT area, subtema FROM questions WHERE id = ?", (record["question_id"],)).fetchone()
                if current != (old["area"], old["subtema"]):
                    raise RuntimeError(f"Questão {record['question_id']} mudou desde o dry-run")
                db.execute(
                    "UPDATE questions SET area = ?, subtema = ?, subtema_id = ? WHERE id = ?",
                    (target["area"], target["subtema"], subtema_ids.get(target["subtema"]), record["question_id"]),
                )
                db.execute(
                    """INSERT INTO reclassification_audit
                       (question_id, old_area, old_subtema, new_area, new_subtema, confidence, rationale, model_used, applied, classified_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                    (record["question_id"], old["area"], old["subtema"], target["area"], target["subtema"], 1.0,
                     f"{run_id}; HAR Medway {record['evidence']['medway_id']}; {match_label}; tags: {', '.join(record['evidence']['tags'])}",
                     model_used, datetime.now(timezone.utc).isoformat()),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        receipt = {"run_id": run_id, "backup": str(backup), "applied": len(changes), "remaining_candidates": max(0, sum(record["status"] in applicable_statuses for record in records) - len(changes)), "report": str(args.report), "input_sha256": input_hash}
        receipt_path = args.report.with_name(f"medway-trilhas-har-apply-{stamp}.json")
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
