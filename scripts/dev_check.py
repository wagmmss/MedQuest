#!/usr/bin/env python3
"""Runner Unificado de Validação em Camadas (Developer Velocity) — MedQuest.

Organiza as validações do repositório em 3 níveis de velocidade e rigor:
- fast     (Commit Local): Execução incremental baseada em diff (< 15s).
- standard (Pre-Push / CI Rápido): Validação do componente alterado (~0-30s).
- full     (Pull Request / Gate de Merge): Build completo de produção, auditorias e SLAs (~2-3 min).

Uso:
    python scripts/dev_check.py --tier=fast
    python scripts/dev_check.py --tier=standard
    python scripts/dev_check.py --tier=full
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "app" / "backend"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"
APP_INFRASTRUCTURE_FILES = {
    "app/backend/Dockerfile",
    "app/backend/.dockerignore",
    "app/frontend/Dockerfile",
    "app/frontend/.dockerignore",
}


def get_git_diff_files():
    """Retorna lista de arquivos modificados (staged + unstaged + untracked)."""
    files = set()
    try:
        # Staged files
        res = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if line.strip():
                files.add(line.strip().replace("\\", "/"))

        # Unstaged files
        res = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if line.strip():
                files.add(line.strip().replace("\\", "/"))

        # Untracked files
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if line.startswith("??"):
                f = line[3:].strip().replace("\\", "/")
                files.add(f)
    except Exception as e:
        print(f"[WARN] Falha ao inspecionar git status: {e}")
    return list(files)


def get_push_diff_files():
    """Retorna os arquivos dos commits locais que ainda serao enviados."""
    try:
        upstream = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if upstream:
            res = subprocess.run(
                ["git", "diff", "--name-only", f"{upstream}...HEAD"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=True,
            )
            return [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        pass

    # Repositorios sem upstream ainda recebem uma validacao proporcional ao
    # ultimo commit. Se nem isso existir, o tier completo continua sendo o
    # fallback seguro.
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD^", "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def map_backend_tests(changed_files):
    """Mapeia arquivos alterados no backend para seus testes unitários correspondentes."""
    test_files = set()
    mapping = {
        "app/backend/api/questions.py": [
            "tests/test_api.py",
            "tests/test_observability.py",
        ],
        "app/backend/api/stats.py": [
            "tests/test_stats_phase1.py",
            "tests/test_exam_readiness.py",
        ],
        "app/backend/api/flashcards.py": [
            "tests/test_flashcards_api.py",
            "tests/test_srs.py",
        ],
        "app/backend/api/plan.py": [
            "tests/test_planner.py",
            "tests/test_observability.py",
        ],
        "app/backend/api/universal_pool.py": [
            "tests/test_universal_pool.py",
            "tests/test_ai_backend.py",
        ],
        "app/backend/api/db.py": [
            "tests/test_idempotency.py",
            "tests/test_turso_transactions.py",
            "tests/test_auth_isolation.py",
            "tests/test_bootstrap.py",
        ],
        "app/backend/api/schemas.py": [
            "tests/test_api.py",
            "tests/test_planner.py",
        ],
        "app/backend/api/observability.py": [
            "tests/test_observability.py",
        ],
        "app/backend/scripts/check_performance_guardrails.py": [
            "tests/test_performance_guardrails.py",
        ],
        "app/backend/api/notifications.py": [
            "tests/test_notifications.py",
        ],
        "app/backend/api/webpush.py": [
            "tests/test_notifications.py",
        ],
    }

    has_backend_changes = False
    for f in changed_files:
        if f in APP_INFRASTRUCTURE_FILES:
            continue
        if f.startswith("app/backend/"):
            has_backend_changes = True
            if f in mapping:
                test_files.update(mapping[f])
            elif f.startswith("app/backend/migrations/"):
                test_files.update(["tests/test_migrations.py", "tests/test_flashcards_api.py"])
            elif f.startswith("app/backend/tests/"):
                rel_test = f.replace("app/backend/", "")
                test_files.add(rel_test)

    # Se houve alteração no backend mas nenhum teste específico mapeado, rodar testes prioritários
    if has_backend_changes and not test_files:
        test_files.update([
            "tests/test_api.py",
            "tests/test_observability.py",
            "tests/test_planner.py",
        ])

    return list(test_files)


def run_command(cmd, cwd, step_name):
    """Executa um comando e retorna (sucesso, tempo_em_segundos)."""
    print(f"--> [{step_name}] Executando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    t0 = time.perf_counter()
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            shell=isinstance(cmd, str),
            text=True,
            check=False,
        )
        elapsed = time.perf_counter() - t0
        if res.returncode == 0:
            print(f"    [OK] {step_name} concluido com sucesso ({elapsed:.2f}s)\n")
            return True, elapsed
        else:
            print(f"    [FAIL] {step_name} falhou com codigo {res.returncode} ({elapsed:.2f}s)\n")
            return False, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"    [FAIL] {step_name} disparou excecao: {e} ({elapsed:.2f}s)\n")
        return False, elapsed


def get_backend_python_cmd():
    """Retorna comando executavel python do backend virtualenv."""
    if os.name == "nt":
        venv_py = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            return str(venv_py)
    else:
        venv_py = BACKEND_DIR / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)
    return sys.executable


def get_backend_pytest_cmd():
    """Retorna comando executavel pytest do backend virtualenv."""
    if os.name == "nt":
        venv_pytest = BACKEND_DIR / ".venv" / "Scripts" / "pytest.exe"
        if venv_pytest.exists():
            return str(venv_pytest)
    else:
        venv_pytest = BACKEND_DIR / ".venv" / "bin" / "pytest"
        if venv_pytest.exists():
            return str(venv_pytest)
    return "pytest"


def run_tier_fast():
    """Camada 1: Fast (Commit Local — Escopo Incremental por Diff)."""
    print("================================================================")
    print("[FAST TIER] MEDQUEST DEV-VELOCITY: COMMIT LOCAL")
    print("================================================================\n")

    changed = get_git_diff_files()
    print(f"Arquivos alterados detectados ({len(changed)}):")
    for f in changed[:8]:
        print(f"  - {f}")
    if len(changed) > 8:
        print(f"  ... e mais {len(changed) - 8} arquivos.")
    print()

    # Se apenas documentação mudou, validação instantânea
    is_only_docs = changed and all(f.startswith("docs/") or f.endswith(".md") or f.endswith(".txt") for f in changed)
    if is_only_docs:
        print("[FAST-BYPASS] Apenas documentacao alterada. Validacao concluida instantaneamente!")
        return True, 0.05

    py_cmd = get_backend_python_cmd()
    pytest_cmd = get_backend_pytest_cmd()

    timings = []
    all_ok = True

    # 1. Backend: Testes do escopo alterado
    backend_tests = map_backend_tests(changed)
    if backend_tests:
        cmd = [pytest_cmd, "-q", "--disable-warnings"] + backend_tests
        ok, el = run_command(cmd, BACKEND_DIR, f"Backend Diff Tests ({len(backend_tests)} suites)")
        timings.append(("Backend Diff Tests", el))
        if not ok:
            all_ok = False
    else:
        print("[-] Backend: Nenhuma alteracao de codigo backend detectada. Pulando testes backend.\n")

    # 2. Frontend: Linter rápido apenas nos arquivos TS/TSX alterados
    frontend_ts_files = [
        str((ROOT_DIR / f).resolve())
        for f in changed
        if (f.startswith("app/frontend/src/") or f.startswith("src/"))
        and (f.endswith(".ts") or f.endswith(".tsx"))
        # Arquivos removidos também aparecem no diff, mas não podem ser
        # enviados ao ESLint. Isso é comum ao substituir uma route handler.
        and (ROOT_DIR / f).is_file()
    ]

    if frontend_ts_files:
        local_bin = FRONTEND_DIR / "node_modules" / ".bin" / ("eslint.cmd" if os.name == "nt" else "eslint")
        rel_files = [os.path.relpath(f, FRONTEND_DIR).replace("\\", "/") for f in frontend_ts_files[:10]]
        if local_bin.exists():
            cmd = [str(local_bin), "--quiet"] + rel_files
        else:
            npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
            cmd = [npx_cmd, "eslint", "--quiet"] + rel_files
        ok, el = run_command(cmd, FRONTEND_DIR, f"Frontend Incremental Lint ({len(frontend_ts_files)} arquivos)")
        timings.append(("Frontend Incremental Lint", el))
        if not ok:
            all_ok = False
    else:
        print("[-] Frontend: Nenhum arquivo TypeScript alterado detectado. Pulando ESLint.\n")

    return all_ok, sum(t[1] for t in timings)


def run_tier_standard():
    """Camada 2: Standard (Pre-Push proporcional aos componentes alterados)."""
    print("================================================================")
    print("[STANDARD TIER] MEDQUEST DEV-VELOCITY: PRE-PUSH")
    print("================================================================")

    py_cmd = get_backend_python_cmd()
    pytest_cmd = get_backend_pytest_cmd()
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"

    timings = []
    all_ok = True

    changed = get_push_diff_files()
    backend_changed = any(
        f.startswith("app/backend/") and f not in APP_INFRASTRUCTURE_FILES for f in changed
    )
    frontend_changed = any(
        f.startswith("app/frontend/") and f not in APP_INFRASTRUCTURE_FILES for f in changed
    )

    print(f"Arquivos a enviar detectados: {len(changed)}")
    if not backend_changed and not frontend_changed:
        print("[STANDARD-BYPASS] Apenas infraestrutura/documentacao mudou; testes de aplicacao ja existentes foram preservados.\n")

    # 1. Backend: Suíte completa hermética de testes
    if backend_changed:
        ok, el = run_command([pytest_cmd, "-q"], BACKEND_DIR, "Backend Pytest Suite (Hermetico)")
        timings.append(("Backend Pytest", el))
        if not ok:
            all_ok = False
    else:
        print("[-] Backend: Nenhuma alteracao de aplicacao a enviar. Pulando suite e guardrails.\n")

    # 2. Backend: Guardrails de Performance SLA
    guardrail_script = BACKEND_DIR / "scripts" / "check_performance_guardrails.py"
    if backend_changed and guardrail_script.exists():
        ok, el = run_command([py_cmd, str(guardrail_script)], BACKEND_DIR, "Performance SLA Guardrails")
        timings.append(("Performance Guardrails", el))
        if not ok:
            all_ok = False

    # 3. Frontend: ESLint (Errors only)
    if frontend_changed:
        ok, el = run_command([npm_cmd, "run", "lint", "--", "--quiet"], FRONTEND_DIR, "Frontend ESLint")
        timings.append(("Frontend Lint", el))
        if not ok:
            all_ok = False

        # 4. Frontend: Typecheck incremental
        ok, el = run_command([npx_cmd, "tsc", "--noEmit"], FRONTEND_DIR, "Frontend TypeCheck (tsc)")
        timings.append(("Frontend TypeCheck", el))
        if not ok:
            all_ok = False

        # 5. Frontend: Performance Budgets
        ok, el = run_command([npm_cmd, "run", "check:performance"], FRONTEND_DIR, "Frontend Bundle Check")
        timings.append(("Bundle Check", el))
        if not ok:
            all_ok = False
    else:
        print("[-] Frontend: Nenhuma alteracao de aplicacao a enviar. Pulando lint, typecheck e bundle.\n")

    return all_ok, sum(t[1] for t in timings)


def run_tier_full():
    """Camada 3: Full (Pull Request / Merge Gate)."""
    print("================================================================")
    print("[FULL TIER] MEDQUEST DEV-VELOCITY: PULL REQUEST / MERGE GATE")
    print("================================================================\n")

    py_cmd = get_backend_python_cmd()
    pytest_cmd = get_backend_pytest_cmd()
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"

    timings = []
    all_ok = True

    # 1. Backend: Pytest completo com Coverage
    ok, el = run_command([pytest_cmd, "--cov=api", "-q"], BACKEND_DIR, "Backend Pytest with Coverage")
    timings.append(("Backend Pytest + Coverage", el))
    if not ok:
        all_ok = False

    # 2. Backend: Performance Guardrails
    guardrail_script = BACKEND_DIR / "scripts" / "check_performance_guardrails.py"
    if guardrail_script.exists():
        ok, el = run_command([py_cmd, str(guardrail_script)], BACKEND_DIR, "Backend SLA Guardrails")
        timings.append(("Backend Guardrails", el))
        if not ok:
            all_ok = False

    # 3. Frontend: Linting
    ok, el = run_command([npm_cmd, "run", "lint", "--", "--max-warnings=0"], FRONTEND_DIR, "Frontend ESLint Strict")
    timings.append(("Frontend Lint", el))
    if not ok:
        all_ok = False

    # 4. Frontend: TypeCheck
    ok, el = run_command([npx_cmd, "tsc", "--noEmit"], FRONTEND_DIR, "Frontend TypeScript Strict Check")
    timings.append(("Frontend TypeCheck", el))
    if not ok:
        all_ok = False

    # 5. Frontend: Full Production Build & Bundle Budget
    ok, el = run_command([npm_cmd, "run", "build"], FRONTEND_DIR, "Frontend Production Next.js Build")
    timings.append(("Frontend Production Build", el))
    if not ok:
        all_ok = False

    return all_ok, sum(t[1] for t in timings)


def main():
    parser = argparse.ArgumentParser(description="Runner de Validação em Camadas — MedQuest")
    parser.add_argument(
        "--tier",
        "-t",
        choices=["fast", "standard", "full"],
        default="fast",
        help="Nivel de validacao: fast (commit), standard (push), full (PR)",
    )
    args = parser.parse_args()

    t_start = time.perf_counter()

    if args.tier == "fast":
        success, duration = run_tier_fast()
    elif args.tier == "standard":
        success, duration = run_tier_standard()
    elif args.tier == "full":
        success, duration = run_tier_full()
    else:
        print(f"[ERRO] Tier desconhecido: {args.tier}")
        sys.exit(1)

    t_total = time.perf_counter() - t_start

    print("----------------------------------------------------------------")
    status_msg = "[PASS] SUCESSO: TODAS AS VALIDACOES PASSARAM" if success else "[FAIL] ERRO: FALHAS DETECTADAS"
    print(f"{status_msg} (Camada: {args.tier.upper()} | Tempo Total: {t_total:.2f}s)")
    print("----------------------------------------------------------------")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
