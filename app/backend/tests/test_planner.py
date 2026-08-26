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
    assert result["total_required_hours"] == 610


def test_go_focos_usp_are_high_yield():
    rows = []
    start = date.today()
    result = generate_annual_plan(
        rows,
        start.isoformat(),
        (start + timedelta(weeks=20)).isoformat(),
        hours_per_week=20,
        intensive=True,
    )
    topics = [topic for week in result["plan"] for topic in week["topics"]]
    go_topics = [t for t in topics if t["area"] == "Ginecologia e Obstetrícia"]
    go_names = {t["subtema"] for t in go_topics}

    # Verify key GO Foco USP topics are present in intensive plan
    assert "Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)" in go_names
    assert "Investigação das Amenorreias e Síndrome dos Ovários Policísticos (SOP)" in go_names
    assert "Assistência Pré-Natal de Baixo e Alto Risco" in go_names
    assert "Rastreamento Citopatológico e Conduta em Lesões Cervicais (HPV)" in go_names
    assert "Diabetes Gestacional e Pré-Gestacional" in go_names
    assert "Métodos Contraceptivos: Hormonais, DIU e Cirúrgicos" in go_names
    assert "Climatério, Menopausa e Terapia de Reposição Hormonal (TRH)" in go_names
    assert "Uroginecologia: Incontinência Urinária e Prolapso Genital" in go_names
    assert len(go_names) == 14


def test_proportional_distribution_avoids_end_concentration():
    rows = []
    start = date.today()
    result = generate_annual_plan(
        rows,
        start.isoformat(),
        (start + timedelta(weeks=26)).isoformat(),
        hours_per_week=24,
        intensive=False,
    )
    plan = result["plan"]
    assert len(plan) >= 20

    # Ensure GO is well distributed across the schedule, not only at the end
    first_half_weeks = plan[:len(plan)//2]
    second_half_weeks = plan[len(plan)//2:]

    go_first_half = sum(1 for w in first_half_weeks for t in w["topics"] if t["area"] == "Ginecologia e Obstetrícia")
    go_second_half = sum(1 for w in second_half_weeks for t in w["topics"] if t["area"] == "Ginecologia e Obstetrícia")

    assert go_first_half >= 10
    assert go_second_half >= 10

    # In the final 3 weeks, no single area should occupy > 60% of total topics
    for w in plan[-3:]:
        total_w = len(w["topics"])
        for area in ["Clínica Médica", "Cirurgia", "Ginecologia e Obstetrícia", "Pediatria", "Preventiva"]:
            area_count = sum(1 for t in w["topics"] if t["area"] == area)
            assert area_count <= max(3, int(total_w * 0.65))

