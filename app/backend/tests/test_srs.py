import json
from datetime import datetime, timezone

from fsrs import Rating

from api.srs import _rating, review


def test_rating_mapping():
    assert _rating(False, "certeza") == Rating.Again
    assert _rating(False, None) == Rating.Again
    assert _rating(True, "chutei") == Rating.Hard
    assert _rating(True, "duvida") == Rating.Good
    assert _rating(True, "certeza") == Rating.Easy
    assert _rating(True, None) == Rating.Good
    assert _rating(True, "unknown_value") == Rating.Good

def test_review_new_card():
    # Simulando primeira resposta (Acerto com duvida -> Good)
    card_json, due_iso = review(None, True, "duvida")
    
    assert card_json is not None
    assert due_iso is not None
    
    card_dict = json.loads(card_json)
    # A initial review with "Good" usually pushes due date a few minutes/days forward
    assert "due" in card_dict
    assert "state" in card_dict

def test_review_existing_card():
    # Cria estado inicial
    card_json_1, _ = review(None, True, "certeza")
    
    # Simula erro na proxima revisao
    card_json_2, due_iso_2 = review(card_json_1, False, None)
    card_dict_2 = json.loads(card_json_2)
    
    # State deve refletir aprendizado
    assert "due" in card_dict_2
    
    # Erro -> Again -> agendamento deve ser para um futuro muito próximo
    due_date_2 = datetime.fromisoformat(due_iso_2)
    assert due_date_2 > datetime.now(timezone.utc)
