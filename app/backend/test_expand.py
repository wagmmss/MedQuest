import os
import sys

# Ensure backend folder is in path
sys.path.insert(0, os.path.abspath("C:/dev/MedQuest/app/backend"))

from dotenv import load_dotenv
load_dotenv("C:/dev/MedQuest/app/backend/.env")

from groq import Groq

def test_expansion(query: str):
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    prompt = f"""Você é um especialista médico focado em buscas. O usuário quer pesquisar o seguinte termo: "{query}"

Retorne um JSON contendo uma lista de strings (phrases). Esta lista deve conter o termo original e de 3 a 7 sinônimos, termos técnicos ou diagnósticos diferenciais intimamente ligados à pesquisa.

Exemplo para "pressao alta": ["pressao alta", "hipertensao", "has", "crise hipertensiva", "pressao arterial"]
Exemplo para "infarto": ["infarto", "iam", "isquemia miocardica", "sindrome coronariana", "supra de st"]

Responda APENAS com o JSON. Exemplo: {{ "terms": ["...", "..."] }}
"""
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "Você responde apenas em JSON válido."}, {"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return str(e)

print(test_expansion("falta de ar"))
