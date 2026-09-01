"""Script de Verificação Automatizada de Guardrails de Performance (CI/CD) — MedQuest.

Executa benchmark hermético rápido dos endpoints críticos e valida se estão dentro dos SLAs.
"""

import math
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import create_app

GUARDRAILS = [
    {
        "name": "Busca FTS5 (/api/search)",
        "url": "/api/search?q=hipertensao&limit=10",
        "max_p95_ms": 30.0,
        "max_payload_kb": 50.0,
        "iterations": 25,
    },
    {
        "name": "Coverage Resumo (/api/coverage?summary_only=true)",
        "url": "/api/coverage?summary_only=true",
        "max_p95_ms": 10.0,
        "max_payload_kb": 5.0,
        "iterations": 25,
    },
    {
        "name": "Stats Overview (/api/stats/overview)",
        "url": "/api/stats/overview",
        "max_p95_ms": 5.0,
        "max_payload_kb": 5.0,
        "iterations": 25,
    },
    {
        "name": "Stats Timeline (/api/stats/timeline?days=14)",
        "url": "/api/stats/timeline?days=14",
        "max_p95_ms": 10.0,
        "max_payload_kb": 10.0,
        "iterations": 25,
    },
]


def percentile(data, p):
    s = sorted(data)
    idx = max(0, math.ceil(len(s) * p) - 1)
    return round(s[idx], 2)


def run_checks():
    print("================================================================")
    print("🔍 MEDQUEST CI: VERIFICAÇÃO AUTOMATIZADA DE GUARDRAILS DE SLA")
    print("================================================================\n")

    app = create_app(testing=True)
    client = app.test_client()

    failed = False

    for g in GUARDRAILS:
        name = g["name"]
        url = g["url"]
        max_p95 = g["max_p95_ms"]
        max_kb = g["max_payload_kb"]
        iters = g["iterations"]

        # Warmup
        client.get(url)

        times = []
        payload_bytes = 0

        for _ in range(iters):
            t0 = time.perf_counter()
            res = client.get(url)
            t1 = time.perf_counter()
            if res.status_code != 200:
                print(f"❌ {name}: HTTP Status {res.status_code} inesperado.")
                failed = True
                break
            times.append((t1 - t0) * 1000)
            payload_bytes = len(res.data)

        if not times:
            continue

        p50 = percentile(times, 0.50)
        p95 = percentile(times, 0.95)
        kb = round(payload_bytes / 1024, 2)

        p95_ok = p95 <= max_p95
        payload_ok = kb <= max_kb

        status_str = "✅ PASSOU" if (p95_ok and payload_ok) else "❌ FALHOU"
        print(f"{status_str} | {name}")
        print(f"       Latência: P50={p50:.2f}ms | P95={p95:.2f}ms (Teto SLA: {max_p95:.1f}ms)")
        print(f"       Payload:  {kb:.2f} KB (Teto SLA: {max_kb:.1f} KB)\n")

        if not p95_ok or not payload_ok:
            failed = True

    if failed:
        print("🚨 ERRO: Regressão de performance detectada! O build foi bloqueado.")
        sys.exit(1)
    else:
        print("🎉 SUCESSO: Todos os endpoints estão dentro dos SLAs de performance.")
        sys.exit(0)


if __name__ == "__main__":
    run_checks()
