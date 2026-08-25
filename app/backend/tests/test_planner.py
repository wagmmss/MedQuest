from datetime import date, timedelta

from scripts.planner import generate_annual_plan


def test_intensive_plan_uses_high_yield_catalog():
    rows = [
        {"area": "Clínica Médica", "subtema": "Hipertensão Arterial Sistêmica e Crises Hipertensivas", "q_count": 12},
        {"area": "Clínica Médica", "subtema": "Tema sem prioridade cadastrada", "q_count": 12},
    ]
    start = date.today()
    result = generate_annual_plan(
        rows,
        start.isoformat(),
        (start + timedelta(weeks=8)).isoformat(),
        hours_per_week=10,
        intensive=True,
    )

    topics = [topic for week in result["plan"] for topic in week["topics"]]
    assert [topic["subtema"] for topic in topics] == ["Hipertensão Arterial Sistêmica e Crises Hipertensivas"]


def test_plan_uses_curriculum_theory_duration_and_two_hour_practice_block():
    rows = [
        {"area": "Clínica Médica", "subtema": "Hipertensão Arterial Sistêmica e Crises Hipertensivas", "q_count": 12},
    ]
    start = date.today()

    result = generate_annual_plan(
        rows,
        start.isoformat(),
        (start + timedelta(weeks=8)).isoformat(),
        hours_per_week=10,
    )

    topic = result["plan"][0]["topics"][0]
    assert topic["estimated_theory_hours"] == 2.81
    assert topic["estimated_practice_hours"] == 2.0
    assert topic["estimated_hours"] == 4.81
    assert topic["theory_source"] == "curriculum"
    assert topic["course_module"] == "Hipertensão Arterial Sistêmica e Crises Hipertensivas"


def test_plan_uses_conservative_fallback_when_course_match_is_uncertain():
    rows = [
        {"area": "Clínica Médica", "subtema": "Tema sem prioridade cadastrada", "q_count": 12},
    ]
    start = date.today()

    result = generate_annual_plan(
        rows,
        start.isoformat(),
        (start + timedelta(weeks=8)).isoformat(),
        hours_per_week=10,
    )

    topic = result["plan"][0]["topics"][0]
    assert topic["estimated_theory_hours"] == 1.0
    assert topic["estimated_practice_hours"] == 2.0
    assert topic["estimated_hours"] == 3.0
    assert topic["theory_source"] == "pedagogical_estimate"
