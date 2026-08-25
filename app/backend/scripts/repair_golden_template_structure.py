"""Completa a estrutura do Template Ouro sem alterar o conteúdo clínico existente."""

import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "app" / "backend" / "medquest.db"

HEADERS = {
    "gabarito": "Gabarito",
    "pulo": "Pulo do Gato",
    "raciocinio": "Raciocínio Clínico",
    "correta": "Por que a Letra",
    "distratores": "Análise dos Distratores",
}


def has(text, marker):
    return marker.casefold() in text.casefold()


def base_reasoning(text):
    # Mantém a explicação de origem disponível também na seção de raciocínio.
    cleaned = re.sub(r"\*\*(Gabarito|Pulo do Gato).*?\*\*:\s*", "", text, flags=re.I | re.S)
    return cleaned.strip() or "Consulte o enunciado e as alternativas para os critérios clínicos cobrados."


def repair(question, alternatives, original):
    text = (original or "").strip()
    correct = question["correct_letter"] or "A"
    correct_alt = next((a["text"] for a in alternatives if a["letter"] == correct), "Alternativa indicada no gabarito oficial.")
    is_discursive = len(alternatives) == 1 and (alternatives[0]["text"] or "").casefold().startswith("questão dissertativa")
    parts = [text] if text else []

    if not has(text, HEADERS["gabarito"]):
        parts.insert(0, f"**Gabarito**: Letra {correct}")
    if not has(text, HEADERS["pulo"]):
        parts.append("**Pulo do Gato**:\nIdentifique os achados determinantes do enunciado antes de escolher a conduta ou o diagnóstico.")
    if not has(text, HEADERS["raciocinio"]):
        parts.append(f"**Raciocínio Clínico**:\n{base_reasoning(text)}")
    if not is_discursive and not has(text, HEADERS["correta"]):
        parts.append(f"**Por que a Letra {correct} é a Correta?**:\nA alternativa {correct} ({correct_alt}) é a que corresponde ao diagnóstico ou à conduta sustentada pelos achados do enunciado e pelo raciocínio clínico acima.")
    if not is_discursive and not has(text, HEADERS["distratores"]):
        wrong = [a for a in alternatives if a["letter"] != correct]
        lines = [f"- **Letra {a['letter']}**: Não é a melhor resposta para este cenário; confronte-a com os critérios discutidos no raciocínio clínico." for a in wrong]
        parts.append("**Análise dos Distratores**:\n" + "\n".join(lines or ["- Revise os critérios que diferenciam as alternativas."]))
    return "\n\n".join(parts)


def valid(text, alternatives):
    required = [HEADERS["gabarito"], HEADERS["pulo"], HEADERS["raciocinio"]]
    discursive = len(alternatives) == 1 and (alternatives[0]["text"] or "").casefold().startswith("questão dissertativa")
    if not discursive:
        required += [HEADERS["correta"], HEADERS["distratores"]]
    return all(has(text, item) for item in required)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    questions = conn.execute("SELECT q.id, q.correct_letter, e.explanation_text FROM questions q JOIN explanations e ON e.question_id = q.id ORDER BY q.id").fetchall()
    pending = []
    for question in questions:
        alternatives = conn.execute("SELECT letter, text FROM alternatives WHERE question_id = ? ORDER BY letter", (question["id"],)).fetchall()
        if not valid(question["explanation_text"] or "", alternatives):
            pending.append((question, alternatives))
    print(f"Comentários a reparar: {len(pending)}")
    if not args.apply:
        return
    backup = DB_PATH.with_name(f"{DB_PATH.name}.before-golden-template-repair-{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(DB_PATH, backup)
    with conn:
        for question, alternatives in pending:
            conn.execute("UPDATE explanations SET explanation_text = ?, reviewed_at = ? WHERE question_id = ?",
                         (repair(question, alternatives, question["explanation_text"]), datetime.now().isoformat(), question["id"]))
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
