"""Importa módulos Medway obtidos por HAR com categorização canônica explícita."""

import argparse
import base64
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from import_medway_autoral import clean_html_to_markdown, extract_gabarito, format_medway_golden_explanation


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
DOWNLOADS = Path(r"C:\Users\wmors\Downloads")
IMPORTS = {
    "burns": {
        "path": DOWNLOADS / "Queimaduras PED.har",
        "source_file": "MEDWAY MÓDULO QUEIMADURAS PED 2026",
        "topic": "Queimaduras",
    },
    "substances": {
        "path": DOWNLOADS / "Abuso de Substâncias.har",
        "source_file": "MEDWAY MÓDULO TRANSTORNOS POR USO DE SUBSTÂNCIAS 2026",
        "topic": "Transtornos por Uso de Substâncias",
    },
    "dislocations": {
        "path": DOWNLOADS / "Luxações.har",
        "source_file": "MEDWAY MÓDULO LUXAÇÕES E LESÕES LIGAMENTARES 2026",
        "topic": "Luxações e Lesões Ligamentares / Meniscais",
    },
    "tendinopathies": {
        "path": DOWNLOADS / "Tendinites.har",
        "source_file": "MEDWAY MÓDULO TENDINOPATIAS E BURSITES 2026",
        "topic": "Tendinopatias, Bursites e Sobrecarga Musculoesquelética",
    },
    "soft_tissue_sarcomas": {
        "path": DOWNLOADS / "Sarcomas.har",
        "source_file": "MEDWAY MÓDULO SARCOMAS DE PARTES MOLES 2026",
        "topic": "Sarcomas de Partes Moles",
    },
}


def content_as_json(entry):
    content = entry.get("response", {}).get("content", {})
    text = content.get("text", "")
    if text and content.get("encoding") == "base64":
        text = base64.b64decode(text).decode("utf-8", errors="ignore")
    return json.loads(text) if text else None


def parse_har(path: Path):
    har = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    questions, explanations, order = {}, {}, []
    for entry in har.get("log", {}).get("entries", []):
        url = entry.get("request", {}).get("url", "")
        try:
            data = content_as_json(entry)
        except Exception:
            continue
        if not data:
            continue
        if "api/v3/track/" in url and "questions" in url:
            items = data if isinstance(data, list) else (data.get("results") or data.get("questions") or [])
            for item in items:
                qid = str(item.get("id"))
                if qid and qid not in order:
                    order.append(qid)
        elif "api/v3/questions/" in url and "text-explanation" in url:
            explanations[url.split("questions/")[1].split("/")[0]] = data
        elif "api/v3/questions/" in url and isinstance(data, dict) and data.get("id"):
            questions[str(data["id"])] = data
    # Alguns HARs não retornam a lista do track completa; mantém ordem de captura.
    if not order:
        order = list(questions)
    return [questions[qid] for qid in order if qid in questions], explanations


def specialty_code(question):
    specialties = question.get("speciality") or []
    if isinstance(specialties, dict):
        specialties = [specialties]
    return " ".join(str(item.get("abbreviation", "")) for item in specialties if isinstance(item, dict)).upper()


def category(kind, question):
    if kind == "substances":
        return "Clínica Médica", "Transtornos por Uso de Substâncias (Álcool, Tabaco e Drogas de Abuso)"
    if kind == "dislocations":
        return "Cirurgia", "Luxações Articulares e Lesões Ligamentares / Meniscais"
    if kind == "tendinopathies":
        return "Cirurgia", "Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética"
    if kind == "soft_tissue_sarcomas":
        return "Cirurgia", "Sarcomas de Partes Moles"
    if "PED" in specialty_code(question):
        return "Cirurgia", "Particularidades das Queimaduras na Faixa Etária Pediátrica"
    return "Cirurgia", "Atendimento ao Paciente Queimado e Reposição Volêmica"


def remove_existing(conn, source_file):
    ids = [row[0] for row in conn.execute("SELECT id FROM questions WHERE source_file = ?", (source_file,))]
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    for table in ("alternatives", "explanations", "question_images"):
        conn.execute(f"DELETE FROM {table} WHERE question_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", ids)
    return len(ids)


def import_one(kind, dry_run):
    config = IMPORTS[kind]
    questions, explanations = parse_har(config["path"])
    categorized = [category(kind, question) for question in questions]
    print(f"{kind}: {len(questions)} questões | {dict((item, categorized.count(item)) for item in set(categorized))}")
    if dry_run:
        return

    backup = DB_PATH.with_name(f"{DB_PATH.name}.before-import-{kind}-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(DB_PATH, backup)
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        removed = remove_existing(conn, config["source_file"])
        for number, question in enumerate(questions, 1):
            qid = str(question["id"])
            explanation = explanations.get(qid, {})
            options = question.get("options") or []
            correct = extract_gabarito(explanation, options) if options else "A"
            area, subtema = category(kind, question)
            stem = clean_html_to_markdown(question.get("content") or "")
            conn.execute("""INSERT INTO questions
                (source_file, source_number, year, institution_code, institution_label, topic, stem,
                 correct_letter, missing_alts, comment_code, area, subtema, editorial_status, status)
                VALUES (?, ?, 2026, 'MEDWAY', 'Medway', ?, ?, ?, 0, ?, ?, ?, 'autoral', 'active')""",
                (config["source_file"], number, config["topic"], stem, correct, f"medway:{qid}", area, subtema),
            )
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            if options:
                for option in options:
                    letter = (option.get("letter") or "").upper()
                    conn.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, ?, ?, ?)",
                                 (new_id, letter, clean_html_to_markdown(option.get("content") or ""), int(letter == correct)))
            else:
                conn.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, 'A', 'Questão dissertativa', 1)", (new_id,))
            conn.execute("INSERT INTO explanations (question_id, explanation_text, generated_at, reviewed_at) VALUES (?, ?, ?, ?)",
                         (new_id, format_medway_golden_explanation(explanation, options, correct, not options), now, now))
    print(f"{kind}: removidas {removed}; inseridas {len(questions)}; backup: {backup}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=IMPORTS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    import_one(args.kind, args.dry_run)


if __name__ == "__main__":
    main()
