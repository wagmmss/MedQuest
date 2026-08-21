"""Deterministic adaptive-learning scoring for study queues and diagnostics."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from fsrs import Card, Scheduler


_scheduler = Scheduler(enable_fuzzing=False)


def _utc(value=None):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def fsrs_metrics(card_json, now=None):
    """Return safe FSRS metrics; corrupt/legacy cards remain usable."""
    if not card_json:
        return {"retrievability": None, "stability": None, "difficulty": None}
    try:
        card = Card.from_dict(json.loads(card_json))
        retrievability = _scheduler.get_card_retrievability(card, _utc(now))
        return {
            "retrievability": round(max(0.0, min(1.0, float(retrievability))), 4),
            "stability": round(float(card.stability), 4) if card.stability is not None else None,
            "difficulty": round(float(card.difficulty), 4) if card.difficulty is not None else None,
        }
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return {"retrievability": None, "stability": None, "difficulty": None}


def topic_priority(attempts, correct, retrievability=None, coverage=0.0):
    """Bayesian error estimate weighted by evidence, memory risk and coverage."""
    attempts = max(0, int(attempts or 0))
    correct = max(0, min(attempts, int(correct or 0)))
    confidence = 1.0 - math.exp(-attempts / 5.0)
    error_estimate = ((attempts - correct) + 2.0) / (attempts + 4.0)
    memory_risk = 0.5 if retrievability is None else 1.0 - retrievability
    coverage_gap = 1.0 - max(0.0, min(1.0, float(coverage or 0.0)))
    score = (0.55 * error_estimate * confidence) + (0.30 * memory_risk) + (0.15 * coverage_gap)
    return round(score, 4), round(confidence, 4)


def _due(next_review_date, now):
    if not next_review_date:
        return False
    try:
        return _utc(next_review_date) <= now
    except (TypeError, ValueError):
        return False


def rank_adaptive_candidates(db, user_id, where, params, limit, now=None):
    """Rank eligible questions without randomness and without cross-user data."""
    now = _utc(now)
    rows = db.execute(
        f"""
        SELECT q.id, q.source_file, q.source_number, q.year, q.institution_code,
               q.institution_label, q.topic, q.area, q.subtema,
               COUNT(a.id) AS attempts, COALESCE(SUM(a.is_correct), 0) AS correct,
               (SELECT a2.is_correct FROM attempts a2
                WHERE a2.user_id = ? AND a2.question_id = q.id
                ORDER BY a2.id DESC LIMIT 1) AS latest_correct,
               sr.next_review_date, sr.fsrs_card
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?
        LEFT JOIN spaced_repetition sr ON sr.question_id = q.id AND sr.user_id = ?
        WHERE {where}
        GROUP BY q.id
        """,
        [user_id, user_id, user_id, *params],
    ).fetchall()

    topic_totals = {}
    for row in rows:
        topic = row["subtema"] or row["topic"] or "Sem tema"
        stats = topic_totals.setdefault(topic, [0, 0])
        stats[0] += row["attempts"]
        stats[1] += row["correct"]

    ranked = []
    for row in rows:
        item = dict(row)
        metrics = fsrs_metrics(item.pop("fsrs_card"), now)
        topic = item["subtema"] or item["topic"] or "Sem tema"
        topic_attempts, topic_correct = topic_totals[topic]
        topic_score, _ = topic_priority(topic_attempts, topic_correct, metrics["retrievability"])
        is_due = _due(item.pop("next_review_date"), now)
        reasons = []
        score = topic_score * 40.0
        if is_due:
            score += 100.0
            reasons.append("review_due")
        if item["latest_correct"] == 0:
            score += 30.0
            reasons.append("latest_attempt_wrong")
        if item["attempts"] == 0:
            score += 20.0
            reasons.append("coverage_gap")
        if metrics["retrievability"] is not None and metrics["retrievability"] < 0.9:
            score += (0.9 - metrics["retrievability"]) * 50.0
            reasons.append("memory_at_risk")
        score -= min(item["attempts"], 10) * 1.5
        item["adaptive_score"] = round(score, 3)
        item["adaptive_reasons"] = reasons or ["balanced_practice"]
        item["retrievability"] = metrics["retrievability"]
        item.pop("attempts", None)
        item.pop("correct", None)
        item.pop("latest_correct", None)
        ranked.append(item)
    ranked.sort(key=lambda item: (-item["adaptive_score"], item["id"]))
    return ranked[:limit]


def build_learning_profile(db, user_id, now=None):
    """Build a transparent personalized diagnosis and daily goal."""
    now = _utc(now)
    rows = db.execute(
        """
        SELECT COALESCE(NULLIF(q.subtema, ''), q.topic) AS topic, MIN(q.area) AS area,
               COUNT(DISTINCT q.id) AS available, COUNT(a.id) AS attempts,
               COUNT(DISTINCT a.question_id) AS answered, COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q LEFT JOIN attempts a ON a.question_id=q.id AND a.user_id=?
        WHERE q.missing_alts=0 AND COALESCE(NULLIF(q.subtema, ''), q.topic) IS NOT NULL
        GROUP BY topic
        """,
        (user_id,),
    ).fetchall()
    fsrs_rows = db.execute(
        """SELECT COALESCE(NULLIF(q.subtema, ''), q.topic) AS topic,
                  sr.fsrs_card, sr.next_review_date
           FROM spaced_repetition sr JOIN questions q ON q.id=sr.question_id
           WHERE sr.user_id=?""",
        (user_id,),
    ).fetchall()
    memory = {}
    due_total = 0
    for row in fsrs_rows:
        metrics = fsrs_metrics(row["fsrs_card"], now)
        bucket = memory.setdefault(row["topic"], {"values": [], "due": 0})
        if metrics["retrievability"] is not None:
            bucket["values"].append(metrics["retrievability"])
        if _due(row["next_review_date"], now):
            bucket["due"] += 1
            due_total += 1

    topics = []
    for row in rows:
        mem = memory.get(row["topic"], {"values": [], "due": 0})
        retrievability = min(mem["values"]) if mem["values"] else None
        coverage = row["answered"] / row["available"] if row["available"] else 0.0
        score, confidence = topic_priority(row["attempts"], row["correct"], retrievability, coverage)
        reasons = []
        if row["attempts"] and row["correct"] / row["attempts"] < 0.65:
            reasons.append("low_accuracy")
        if mem["due"]:
            reasons.append("reviews_due")
        if retrievability is not None and retrievability < 0.9:
            reasons.append("memory_at_risk")
        if coverage < 0.2:
            reasons.append("low_coverage")
        topics.append({
            "topic": row["topic"], "area": row["area"], "available": row["available"],
            "attempts": row["attempts"], "correct": row["correct"],
            "accuracy": round(row["correct"] / row["attempts"], 4) if row["attempts"] else None,
            "coverage": round(coverage, 4), "confidence": confidence,
            "retrievability": retrievability, "due_count": mem["due"],
            "priority_score": score, "reasons": reasons or ["balanced_practice"],
        })
    topics.sort(key=lambda item: (-item["priority_score"], item["topic"]))
    config = db.execute(
        "SELECT questions_per_day, target_score, exam_date FROM planner_config WHERE user_id=?",
        (user_id,),
    ).fetchone()
    daily_goal = int(config["questions_per_day"] if config and config["questions_per_day"] else 30)
    return {
        "generated_at": now.isoformat(),
        "goal": {
            "questions_today": max(daily_goal, due_total), "configured_daily_questions": daily_goal,
            "reviews_due": due_total, "target_score": config["target_score"] if config else None,
            "exam_date": config["exam_date"] if config else None,
        },
        "topics": topics[:15],
        "method": {
            "deterministic": True,
            "signals": ["FSRS retrievability", "accuracy with evidence confidence", "coverage", "due reviews"],
        },
    }
