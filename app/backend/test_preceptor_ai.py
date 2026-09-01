import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

sys.path.insert(0, os.path.dirname(__file__))
from api.ai import ask_preceptor_ai

res = ask_preceptor_ai(
    stem="Paciente de 30 anos com dor abdominal...",
    alternatives=[{"letter": "A", "text": "Apendicite", "is_correct": True}],
    correct_letter="A",
    correct_text="Apendicite",
    user_letter="A",
    user_question="Por que não é colecistite?",
    explanation="O quadro é clássico de apendicite.",
    area="Cirurgia",
    subtema="Abdome Agudo"
)
print(res)
