import os
import re

directory = r"c:\dev\MedQuest"
exclude_dirs = {'.git', 'node_modules', '.next', '__pycache__', 'venv', 'dist', 'build'}

for root, dirs, files in os.walk(directory):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith((".py", ".json", ".md", ".ts", ".tsx", ".html", ".js")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            new_content = content
            # Replace regra de ouro
            new_content = new_content.replace("Regra de Ouro", "Regra de Ouro")
            new_content = new_content.replace("Regra de Ouro", "Regra de Ouro")
            new_content = new_content.replace("regra de ouro", "regra de ouro")
            new_content = new_content.replace("REGRA DE OURO", "REGRA DE OURO")

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
