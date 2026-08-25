"""Classifica questões novas sem API, a partir do corpus rotulado anterior.

O modelo é um Naive Bayes multinomial local, treinado com ``topic`` e
``stem`` do backup categorizado. Ele só altera pares área/subtema que não
fazem parte da taxonomia canônica atual; portanto, as recuperações exatas do
backup permanecem intocadas. Cada alteração recebe uma linha de auditoria.
"""

import argparse
import collections
import json
import math
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"
BACKUP_PATH = ROOT / "app" / "backend" / "medquest.db.backup_images_20260824_220955"
TAXONOMY_PATH = ROOT / "app" / "backend" / "data" / "taxonomy.json"


def tokens(value: str) -> list[str]:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z0-9]{2,}", text)
    return words + [f"{left}_{right}" for left, right in zip(words, words[1:])]


def document(question) -> list[str]:
    # O tópico é uma pista clínica de alta qualidade e recebe peso maior,
    # enquanto o enunciado mantém o classificador útil para temas inéditos.
    return tokens((question["topic"] or "") + " ") * 5 + tokens(question["stem"] or "")


def train(rows):
    docs_by_label = collections.Counter()
    words_by_label = collections.defaultdict(collections.Counter)
    totals = collections.Counter()
    vocabulary = set()
    for row in rows:
        label = (row["area"], row["subtema"])
        docs_by_label[label] += 1
        for token in document(row):
            words_by_label[label][token] += 1
            totals[label] += 1
            vocabulary.add(token)
    vocabulary_size = len(vocabulary)
    # Índice invertido: evita avaliar cada token contra todos os 164 módulos.
    token_scores = collections.defaultdict(dict)
    base_scores = {}
    total_docs = sum(docs_by_label.values())
    for label, count in docs_by_label.items():
        denominator = totals[label] + vocabulary_size
        base_scores[label] = (math.log(count / total_docs), math.log(denominator))
        for token, frequency in words_by_label[label].items():
            token_scores[token][label] = math.log(frequency + 0.25) - math.log(0.25)
    return docs_by_label, base_scores, token_scores


def predict(question, model, lock_area=True):
    docs_by_label, base_scores, token_scores = model
    doc_tokens = collections.Counter(document(question))
    length = sum(doc_tokens.values())
    scores = {label: prior - length * log_den for label, (prior, log_den) in base_scores.items()}
    for token, frequency in doc_tokens.items():
        for label, boost in token_scores.get(token, {}).items():
            scores[label] += frequency * boost
    if lock_area:
        allowed = [(score, label) for label, score in scores.items() if label[0] == question["area"]]
        if allowed:
            scores = allowed
        else:
            scores = [(score, label) for label, score in scores.items()]
    else:
        scores = [(score, label) for label, score in scores.items()]
    scores.sort(reverse=True)
    margin = scores[0][0] - scores[1][0] if len(scores) > 1 else 0.0
    # Conversão monotônica do intervalo de log-verossimilhança em confiança.
    confidence = 1 - math.exp(-min(margin, 25))
    return scores[0][1], max(0.50, min(confidence, 0.999))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--backup", type=Path, default=BACKUP_PATH)
    parser.add_argument("--unlock-area", action="store_true", help="Permite que o classificador altere a grande área")
    args = parser.parse_args()

    with open(TAXONOMY_PATH, encoding="utf-8") as file:
        taxonomy = json.load(file)
    canonical = {(area["area"], theme["theme"]) for area in taxonomy for theme in area["macroThemes"]}

    old = sqlite3.connect(args.backup)
    old.row_factory = sqlite3.Row
    training_rows = old.execute("SELECT area, subtema, topic, stem FROM questions").fetchall()
    model = train(training_rows)

    current = sqlite3.connect(args.db)
    current.row_factory = sqlite3.Row
    candidates = current.execute("SELECT id, area, subtema, topic, stem FROM questions ORDER BY id").fetchall()
    candidates = [row for row in candidates if (row["area"], row["subtema"]) not in canonical]

    predictions = []
    for question in candidates:
        (area, subtema), confidence = predict(question, model, lock_area=not args.unlock_area)
        predictions.append((area, subtema, confidence, question))

    print(f"Treinamento: {len(training_rows)} questões / {len(model[0])} módulos observados")
    print(f"Questões novas a classificar: {len(predictions)}")
    print(f"Confiança mediana: {sorted(item[2] for item in predictions)[len(predictions)//2]:.3f}" if predictions else "Sem pendências")
    if not args.apply:
        return

    output_backup = args.db.with_name(f"{args.db.name}.before-local-classification-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(args.db, output_backup)
    now = datetime.now(timezone.utc).isoformat()
    with current:
        for area, subtema, confidence, question in predictions:
            current.execute(
                """INSERT INTO reclassification_audit
                   (question_id, old_area, old_subtema, new_area, new_subtema,
                    confidence, rationale, model_used, applied, classified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (question["id"], question["area"], question["subtema"], area, subtema,
                 confidence, "Classificação local treinada no corpus categorizado anterior.",
                 "local-naive-bayes-backup-corpus", now),
            )
            current.execute("UPDATE questions SET area = ?, subtema = ? WHERE id = ?", (area, subtema, question["id"]))
    print(f"Backup pré-classificação: {output_backup}")


if __name__ == "__main__":
    main()
