import os
import sys
from dotenv import load_dotenv
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
sys.path.insert(0, os.path.dirname(__file__))

from api.ai import ask_preceptor_ai

try:
    res = ask_preceptor_ai(
        stem="Analise o ECG e determine o ritmo.",
        alternatives=[{"letter": "A", "text": "Ritmo sinusal", "is_correct": False}, {"letter": "B", "text": "Ritmo juncional", "is_correct": True}],
        correct_letter="B",
        correct_text="Ritmo juncional",
        user_letter="",
        user_question="O que é ritmo juncional?",
        explanation="O ritmo juncional tem ondas P retrógradas.",
        area="Clínica Médica",
        subtema="Cardiologia"
    )
    import json
    print(json.dumps(res, ensure_ascii=False, indent=2))
except Exception as e:
    traceback.print_exc()
