# -*- coding: utf-8 -*-
"""
Empacota apenas o necessário para hospedar o MedQuest em 'medquest_deploy.zip'
(na pasta MedQuest). Rode SEMPRE que quiser subir uma versão atualizada.

    python make_deploy_zip.py

Inclui: backend/app.py, backend/requirements-web.txt, backend/medquest.db e todo o static/.
Exclui: PDFs, o instalador do WebStorm, __pycache__, backups .bak e os scripts locais.
"""
import os
import zipfile

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BACKEND_DIR)                 # .../MedQuest/app
ROOT_DIR = os.path.dirname(APP_DIR)                    # .../MedQuest
OUT = os.path.join(ROOT_DIR, "medquest_deploy.zip")

INCLUDE_BACKEND = ["app.py", "planner.py", "requirements-web.txt", "medquest.db"]

def add_file(zf, abs_path, arc_path):
    if os.path.exists(abs_path):
        zf.write(abs_path, arc_path)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    # backend essencial
    for name in INCLUDE_BACKEND:
        add_file(zf, os.path.join(BACKEND_DIR, name), f"backend/{name}")

    # pacote api/ (blueprints, db, srs FSRS, schemas, config)
    api_dir = os.path.join(BACKEND_DIR, "api")
    for base, dirs, files in os.walk(api_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                abs_path = os.path.join(base, f)
                rel = os.path.relpath(abs_path, BACKEND_DIR)   # ex.: api/questions.py
                zf.write(abs_path, f"backend/{rel.replace(os.sep, '/')}")

    # static inteiro (css, js, imagens, ícones, sw.js, manifest, index.html)
    static_dir = os.path.join(APP_DIR, "static")
    for base, dirs, files in os.walk(static_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            abs_path = os.path.join(base, f)
            rel = os.path.relpath(abs_path, APP_DIR)          # ex.: static/js/app.js
            zf.write(abs_path, rel.replace(os.sep, "/"))

size_mb = os.path.getsize(OUT) / (1024 * 1024)
print(f"Pacote criado: {OUT}")
print(f"Tamanho: {size_mb:.1f} MB")
