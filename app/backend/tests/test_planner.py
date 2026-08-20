from datetime import date, timedelta

from scripts.planner import generate_annual_plan


def test_intensive_plan_uses_high_yield_catalog():
    rows = [
        {"area": "Clínica Médica", "subtema": "Hipertensão Arterial Sistêmica", "q_count": 12},
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
    assert [topic["subtema"] for topic in topics] == ["Hipertensão Arterial Sistêmica"]
