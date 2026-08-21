from datetime import date, timedelta

from api.stats import responsible_streak


def test_planned_rest_day_preserves_but_does_not_inflate_streak():
    today = date(2026, 8, 20)
    studied = {str(today - timedelta(days=offset)) for offset in (0, 1, 3, 4, 5, 6)}
    result = responsible_streak(studied, today, days_per_week=6)
    assert result["days"] == 6
    assert result["policy"] == "rest_days_preserve_continuity"


def test_excess_unplanned_gap_breaks_streak():
    today = date(2026, 8, 20)
    studied = {str(today), str(today - timedelta(days=3))}
    result = responsible_streak(studied, today, days_per_week=6)
    assert result["days"] == 1


def test_rest_days_never_count_as_active_days():
    today = date(2026, 8, 20)
    result = responsible_streak(set(), today, days_per_week=5)
    assert result["days"] == 0
