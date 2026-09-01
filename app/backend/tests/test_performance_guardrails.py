from scripts.check_performance_guardrails import run_checks


def test_performance_guardrails_pass():
    """Garante que a rotina de guardrails de SLA executa hermeticamente e aprova todos os endpoints."""
    success = run_checks()
    assert success is True


def test_performance_guardrails_fails_on_radar_sla_breach():
    """Garante que o guardrail bloqueia o build se o endpoint do Radar violar seu SLA."""
    strict_guardrail = [
        {
            "name": "Stats Radar de Bancas (SLA Estrito Violado)",
            "url": "/api/stats/institution-radar?institution=USP-SP&compare_institution=UNICAMP",
            "max_p95_ms": 0.0001,  # Impossível de atingir
            "max_payload_kb": 10.0,
            "iterations": 5,
        }
    ]
    success = run_checks(guardrails=strict_guardrail)
    assert success is False

