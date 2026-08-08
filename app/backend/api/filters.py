"""Construção das cláusulas de filtro da fila de estudo (compartilhado por rotas)."""
from datetime import datetime, timezone
from flask import g


def question_filter_clauses(args):
    clauses = ["q.missing_alts = 0"]
    params = []

    institutions = args.getlist("institution")
    if institutions:
        clauses.append(f"q.institution_code IN ({','.join('?' * len(institutions))})")
        params.extend(institutions)

    years = args.getlist("year")
    if years:
        clauses.append(f"q.year IN ({','.join('?' * len(years))})")
        params.extend(years)

    sources = args.getlist("source")
    if sources:
        clauses.append(f"q.source_file IN ({','.join('?' * len(sources))})")
        params.extend(sources)

    areas = args.getlist("area")
    if areas:
        clauses.append(f"q.area IN ({','.join('?' * len(areas))})")
        params.extend(areas)

    subtemas = args.getlist("subtema")
    if subtemas:
        clauses.append(f"q.subtema IN ({','.join('?' * len(subtemas))})")
        params.extend(subtemas)

    status = args.get("status", "all")
    if status == "unanswered":
        clauses.append("q.id NOT IN (SELECT question_id FROM attempts WHERE user_id = ?)")
        params.append(g.user_id)
    elif status == "wrong":
        clauses.append("""q.id IN (
            SELECT question_id FROM attempts a1 WHERE a1.user_id = ? AND a1.is_correct = 0
            AND a1.id = (SELECT MAX(a2.id) FROM attempts a2 WHERE a2.user_id = ? AND a2.question_id = a1.question_id)
        )""")
        params.extend([g.user_id, g.user_id])
    elif status == "answered":
        clauses.append("q.id IN (SELECT question_id FROM attempts WHERE user_id = ?)")
        params.append(g.user_id)
    elif status == "srs_due":
        clauses.append("q.id IN (SELECT question_id FROM spaced_repetition WHERE user_id = ? AND next_review_date <= ?)")
        params.extend([g.user_id, datetime.now(timezone.utc).isoformat()])

    if args.get("favorite") == "1":
        clauses.append("q.id IN (SELECT question_id FROM favorites WHERE user_id = ?)")
        params.append(g.user_id)

    if args.get("id"):
        clauses.append("q.id = ?")
        params.append(args.get("id"))

    return clauses, params
