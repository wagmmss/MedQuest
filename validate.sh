#!/usr/bin/env bash
# Script de validação rápida em camadas para MedQuest (Bash/Linux/CI)
set -e

TIER="${1:-fast}"

PYTHON_BIN="python3"
if [ -f "app/backend/.venv/bin/python" ]; then
    PYTHON_BIN="app/backend/.venv/bin/python"
fi

"$PYTHON_BIN" scripts/dev_check.py --tier "$TIER"
