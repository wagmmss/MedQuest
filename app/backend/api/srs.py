"""Repetição espaçada com FSRS (estado da arte), substituindo o SM-2 simplificado.

Mapeia a resposta da questão para uma nota FSRS:
  - errou               -> Again
  - acertou + "chutei"  -> Hard
  - acertou + "duvida"  -> Good
  - acertou + "certeza" -> Easy
  - acertou (sem info)  -> Good
"""
import json
from datetime import timezone

from fsrs import Scheduler, Card, Rating

_scheduler = Scheduler()

_CONFIDENCE_MAP = {
    "chutei": Rating.Hard,
    "duvida": Rating.Good,
    "certeza": Rating.Easy,
}


def _rating(is_correct, confidence):
    if not is_correct:
        return Rating.Again
    return _CONFIDENCE_MAP.get((confidence or "").lower(), Rating.Good)


def review(card_json, is_correct, confidence=None):
    """Recebe o estado do card (JSON ou None) e devolve (novo_json, próxima_revisão_iso)."""
    card = Card.from_dict(json.loads(card_json)) if card_json else Card()
    card, _log = _scheduler.review_card(card, _rating(is_correct, confidence))
    due_iso = card.due.astimezone(timezone.utc).isoformat()
    return json.dumps(card.to_dict()), due_iso
