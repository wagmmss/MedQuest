import os
import sys

# Ensure backend folder is in path
sys.path.insert(0, os.path.abspath("C:/dev/MedQuest/app/backend"))

from dotenv import load_dotenv

load_dotenv("C:/dev/MedQuest/app/backend/.env")

from api.ai import generate_cloze_flashcard

res = generate_cloze_flashcard(
    stem="Um paciente de 30 anos chega com dispneia...",
    correct_text="Dar oxigênio",
    wrong_text="Dar antibiótico",
    explanation="O oxigênio resolve a hipoxemia imediata."
)

print(res)
