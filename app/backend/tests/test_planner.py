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
    topic_names = {topic["subtema"] for topic in topics}
    assert "Hipertensão Arterial Sistêmica e Crises Hipertensivas" in topic_names
    assert "Tema sem prioridade cadastrada" not in topic_names


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

    topics = [topic for week in result["plan"] for topic in week["topics"]]
    topic = next(topic for topic in topics if topic["subtema"] == "Hipertensão Arterial Sistêmica e Crises Hipertensivas")
    assert topic["estimated_theory_hours"] == 2.81
    assert topic["estimated_practice_hours"] == 2.0
    assert topic["estimated_hours"] == 4.81
    assert topic["theory_source"] == "curriculum"
    assert topic["course_module"] == "Hipertensão Arterial Sistêmica e Crises Hipertensivas"


def test_plan_ignores_topics_outside_the_canonical_catalog():
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

    topics = [topic for week in result["plan"] for topic in week["topics"]]
    assert topics
    assert len({topic["subtema"] for topic in topics}) <= 170
    assert "Tema sem prioridade cadastrada" not in {topic["subtema"] for topic in topics}
    assert result["total_required_hours"] == 610
