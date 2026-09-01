"""Faz uma chamada minima a cada provedor sem imprimir chaves ou respostas."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.universal_pool import generate_content_with_fallback


def main() -> None:
    original_order = os.environ.get("AI_PROVIDER_ORDER")
    original_gemini_budget = os.environ.get("AI_GEMINI_TIMEOUT_BUDGET")
    try:
        os.environ["AI_GEMINI_TIMEOUT_BUDGET"] = "6"
        for provider in ("gemini", "groq", "openrouter", "ollama"):
            os.environ["AI_PROVIDER_ORDER"] = provider
            try:
                result = generate_content_with_fallback("Responda apenas: OK", timeout=5)
                print(f"{provider}: OK ({result['model']}, {len(result['text'])} chars)")
            except Exception as error:
                print(f"{provider}: INDISPONIVEL ({type(error).__name__})")
    finally:
        if original_order is None:
            os.environ.pop("AI_PROVIDER_ORDER", None)
        else:
            os.environ["AI_PROVIDER_ORDER"] = original_order
        if original_gemini_budget is None:
            os.environ.pop("AI_GEMINI_TIMEOUT_BUDGET", None)
        else:
            os.environ["AI_GEMINI_TIMEOUT_BUDGET"] = original_gemini_budget


if __name__ == "__main__":
    main()
