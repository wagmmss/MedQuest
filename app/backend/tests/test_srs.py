"""Testes unitários do SRS (FSRS)."""
from fsrs import Rating

from api import srs


def test_rating_errou_e_again():
    assert srs._rating(False, None) == Rating.Again
    assert srs._rating(False, "certeza") == Rating.Again  # errou ignora confiança


def test_rating_por_confianca():
    assert srs._rating(True, "certeza") == Rating.Easy
    assert srs._rating(True, "duvida") == Rating.Good
    assert srs._rating(True, "chutei") == Rating.Hard
    assert srs._rating(True, None) == Rating.Good


def test_review_gera_card_e_data():
    card_json, due = srs.review(None, True, "certeza")
    assert isinstance(card_json, str) and card_json.startswith("{")
    assert "T" in due  # ISO datetime


def test_review_reusa_card_existente():
    c1, _ = srs.review(None, True, "duvida")
    c2, due2 = srs.review(c1, True, "certeza")
    assert isinstance(c2, str) and "T" in due2
