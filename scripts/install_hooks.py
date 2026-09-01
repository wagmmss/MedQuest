#!/usr/bin/env python3
"""Instalador automatizado de Git Hooks de Alta Velocidade — MedQuest.

Configura:
- pre-commit : Executa validação rápida incremental (< 15s)
- pre-push   : Valida apenas os componentes enviados (~0-30s)
"""

import os
import stat
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT_DIR / ".git" / "hooks"

PRE_COMMIT_SCRIPT = """#!/usr/bin/env bash
# MedQuest Pre-Commit Hook (Tier: Fast)
echo "[MedQuest Pre-Commit] Executando validacoes essenciais da camada fast..."

PYTHON_BIN="python"
if [ -f "app/backend/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="app/backend/.venv/Scripts/python.exe"
elif [ -f "app/backend/.venv/bin/python" ]; then
    PYTHON_BIN="app/backend/.venv/bin/python"
fi

$PYTHON_BIN scripts/dev_check.py --tier=fast
"""

PRE_PUSH_SCRIPT = """#!/usr/bin/env bash
# MedQuest Pre-Push Hook (Tier: Standard)
echo "[MedQuest Pre-Push] Validando os componentes alterados antes do push..."

PYTHON_BIN="python"
if [ -f "app/backend/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="app/backend/.venv/Scripts/python.exe"
elif [ -f "app/backend/.venv/bin/python" ]; then
    PYTHON_BIN="app/backend/.venv/bin/python"
fi

$PYTHON_BIN scripts/dev_check.py --tier=standard
"""


def install_hooks():
    if not HOOKS_DIR.exists():
        print(f"[ERRO] Diretorio de hooks {HOOKS_DIR} nao encontrado. O git esta inicializado?")
        return False

    pre_commit_path = HOOKS_DIR / "pre-commit"
    pre_push_path = HOOKS_DIR / "pre-push"

    pre_commit_path.write_text(PRE_COMMIT_SCRIPT, encoding="utf-8")
    pre_push_path.write_text(PRE_PUSH_SCRIPT, encoding="utf-8")

    # Garante permissões de execução em sistemas Unix
    for hook_file in [pre_commit_path, pre_push_path]:
        try:
            st = os.stat(hook_file)
            os.chmod(hook_file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

    print("================================================================")
    print("[SUCCESS] GIT HOOKS INSTALADOS COM SUCESSO NO MEDQUEST")
    print("================================================================")
    print(f"  - Pre-commit: {pre_commit_path} -> dev_check.py --tier=fast")
    print(f"  - Pre-push:   {pre_push_path} -> dev_check.py --tier=standard")
    print("\nPara desativar temporariamente um hook em commits de emergencia:")
    print("  git commit -m 'mensagem' --no-verify")
    print("  git push --no-verify")
    return True


if __name__ == "__main__":
    install_hooks()
