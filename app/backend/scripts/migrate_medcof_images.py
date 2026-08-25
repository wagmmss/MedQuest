"""
Script de Migração e Download das Imagens do Medcof para Armazenamento Local.
- Baixa todas as 461 imagens do S3 do Medcof para app/backend/static/images/medcof/.
- Registra as imagens de enunciado na tabela canônica question_images.
- Limpa a sintaxe crua de Markdown/HTML dos enunciados (questions.stem).
- Atualiza os links das explicações (explanations.explanation_text) para /api/images/medcof/explanations/....
- Reindexa o FTS (questions_fts) e cria backup de segurança antes da execução.
"""

import os
import re
import sys
import shutil
import sqlite3
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "medquest.db")
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
MEDCOF_IMG_DIR = os.path.join(STATIC_DIR, "images", "medcof")

def get_extension_from_bytes(data: bytes, content_type: str = "") -> str:
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    elif data.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    elif data.startswith(b'RIFF') and b'WEBP' in data[:16]:
        return '.webp'
    elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return '.gif'
    elif data.startswith(b'<svg') or b'<svg' in data[:100]:
        return '.svg'
    elif 'png' in content_type.lower():
        return '.png'
    elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
        return '.jpg'
    elif 'webp' in content_type.lower():
        return '.webp'
    elif 'gif' in content_type.lower():
        return '.gif'
    return '.png'

def download_image(url: str, dest_dir: str, base_filename: str) -> tuple[str, str, int]:
    """
    Baixa uma imagem da URL, determina extensão pelos bytes/header, salva no disco e retorna (url, rel_path, size).
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
    )

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = resp.read()
                ct = resp.headers.get('Content-Type', '')
                ext = get_extension_from_bytes(data, ct)
                
                os.makedirs(dest_dir, exist_ok=True)
                full_filename = f"{base_filename}{ext}"
                full_path = os.path.join(dest_dir, full_filename)
                
                with open(full_path, 'wb') as f:
                    f.write(data)
                    
                rel_path = os.path.relpath(full_path, STATIC_DIR).replace('\\', '/')
                return url, rel_path, len(data)
        except Exception as e:
            last_err = e
            
    raise RuntimeError(f"Falha ao baixar {url} após 3 tentativas: {last_err}")

def main():
    print("="*80)
    print("INICIANDO MIGRAÇÃO DAS IMAGENS DO MEDCOF PARA O MEDQUEST")
    print("="*80)

    # 1. Backup de segurança
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKEND_DIR, f"medquest.db.backup_images_{timestamp}")
    print(f"Criando backup de segurança do banco de dados em:\n  -> {backup_path}")
    shutil.copy2(DB_PATH, backup_path)
    print("[OK] Backup criado com sucesso.\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 2. Identificar imagens em enunciados (Stems)
    print("Mapeando imagens em enunciados (Stems)...")
    questions = cur.execute("SELECT id, source_file, source_number, stem FROM questions").fetchall()
    
    stem_tasks = [] # (qid, source_file, source_number, order_idx, url, dest_dir, base_name)
    url_to_rel_path = {} # Cache de download: url -> rel_path

    for q in questions:
        stem = q['stem'] or ""
        urls = []
        # Encontrar todas as tags markdown ![...](url)
        for m in re.finditer(r'!\[(.*?)\]\((https?://[^\s\)]+)\)', stem):
            u = m.group(2)
            if 'medcof' in u.lower() or 'amazonaws' in u.lower():
                urls.append(u)
        # Encontrar tags html <img src="url">
        for m in re.finditer(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', stem):
            u = m.group(1)
            if 'medcof' in u.lower() or 'amazonaws' in u.lower() and u not in urls:
                urls.append(u)
        # Encontrar URLs avulsas do Medcof no stem se houver
        for m in re.finditer(r'https?://[^\s\)\"\'>]+', stem):
            u = m.group(0)
            if ('medcof' in u.lower() or 'amazonaws' in u.lower()) and u not in urls:
                urls.append(u)

        if urls:
            src = q['source_file']
            if 'USP-RP' in src:
                sub_folder = 'usp_rp'
            elif 'USP-SP' in src:
                sub_folder = 'usp_sp'
            elif 'UNIFESP' in src:
                sub_folder = 'unifesp'
            else:
                sub_folder = 'general'

            dest_dir = os.path.join(MEDCOF_IMG_DIR, sub_folder)
            for idx, u in enumerate(urls):
                base_name = f"q{q['id']}_stem_{idx}"
                stem_tasks.append((q['id'], src, q['source_number'], idx, u, dest_dir, base_name))

    print(f"Total de imagens mapeadas em enunciados: {len(stem_tasks)} (em {len(set(t[0] for t in stem_tasks))} questões)")

    # 3. Identificar imagens em explicações (Explanations)
    print("Mapeando imagens em explicações (Explanations)...")
    explanations = cur.execute("SELECT question_id, explanation_text FROM explanations").fetchall()
    exp_tasks = [] # (qid, order_idx, url, dest_dir, base_name)
    
    exp_dest_dir = os.path.join(MEDCOF_IMG_DIR, "explanations")

    for exp in explanations:
        txt = exp['explanation_text'] or ""
        urls = []
        for m in re.finditer(r'!\[(.*?)\]\((https?://[^\s\)]+)\)', txt):
            u = m.group(2)
            if 'medcof' in u.lower() or 'amazonaws' in u.lower():
                urls.append(u)
        for m in re.finditer(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', txt):
            u = m.group(1)
            if 'medcof' in u.lower() or 'amazonaws' in u.lower() and u not in urls:
                urls.append(u)
        for m in re.finditer(r'https?://[^\s\)\"\'>]+', txt):
            u = m.group(0)
            if ('medcof' in u.lower() or 'amazonaws' in u.lower()) and u not in urls:
                urls.append(u)

        if urls:
            for idx, u in enumerate(urls):
                base_name = f"q{exp['question_id']}_exp_{idx}"
                exp_tasks.append((exp['question_id'], idx, u, exp_dest_dir, base_name))

    print(f"Total de imagens mapeadas em explicações: {len(exp_tasks)} (em {len(set(t[0] for t in exp_tasks))} questões)\n")

    # 4. Compilar fila única de downloads
    all_download_jobs = []
    seen_urls = set()

    for item in stem_tasks:
        qid, src, snum, idx, url, dest_dir, base_name = item
        if url not in seen_urls:
            seen_urls.add(url)
            all_download_jobs.append((url, dest_dir, base_name))

    for item in exp_tasks:
        qid, idx, url, dest_dir, base_name = item
        if url not in seen_urls:
            seen_urls.add(url)
            all_download_jobs.append((url, dest_dir, base_name))

    print(f"Total de downloads únicos a realizar: {len(all_download_jobs)}")
    print("Iniciando download multithread (12 workers)...")

    download_success = 0
    download_errors = []

    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_job = {
            executor.submit(download_image, url, dest_dir, base_name): (url, base_name)
            for url, dest_dir, base_name in all_download_jobs
        }

        for future in as_completed(future_to_job):
            url, base_name = future_to_job[future]
            try:
                orig_url, rel_path, size_bytes = future.result()
                url_to_rel_path[orig_url] = rel_path
                download_success += 1
                if download_success % 50 == 0 or download_success == len(all_download_jobs):
                    print(f"  Progresso: {download_success}/{len(all_download_jobs)} imagens baixadas...")
            except Exception as e:
                download_errors.append((url, str(e)))
                print(f"[ERRO DOWNLOAD] {url}: {e}")

    print(f"\n[DOWNLOAD CONCLUÍDO] Sucesso: {download_success} | Erros: {len(download_errors)}")
    if download_errors:
        print("[AVISO] Alguns downloads falharam. Detalhes:")
        for u, err in download_errors:
            print(f"  - {u}: {err}")

    # 5. Atualizar Banco de Dados
    print("\nAtualizando tabelas do banco de dados...")
    
    # 5.1 Atualizar question_images e limpar stems
    print("1/3 Atualizando question_images e limpando enunciados...")
    stems_updated = 0
    qi_inserted = 0

    # Agrupar stem_tasks por question_id
    stem_by_qid = {}
    for item in stem_tasks:
        qid = item[0]
        stem_by_qid.setdefault(qid, []).append(item)

    for qid, tasks in stem_by_qid.items():
        q_row = cur.execute("SELECT stem FROM questions WHERE id = ?", (qid,)).fetchone()
        if not q_row:
            continue
            
        old_stem = q_row['stem']
        clean_stem = old_stem

        # Remover tags de imagem do stem
        clean_stem = re.sub(r'!\[.*?\]\((https?://[^\s\)]+)\)', '', clean_stem)
        clean_stem = re.sub(r'<img[^>]+src=["\'](https?://[^"\']+)["\'][^>]*>', '', clean_stem)
        # Remover URLs residuais do medcof que ficaram soltas
        clean_stem = re.sub(r'https?://medcof-assets[^\s\)\"\'>]+', '', clean_stem)
        clean_stem = re.sub(r'\n{3,}', '\n\n', clean_stem).strip()

        # Inserir em question_images se tiver download concluído
        cur.execute("DELETE FROM question_images WHERE question_id = ?", (qid,))

        for order_idx, t in enumerate(tasks):
            url = t[4]
            rel_path = url_to_rel_path.get(url)
            if rel_path:
                cur.execute("""
                    INSERT INTO question_images (question_id, file_path, order_index)
                    VALUES (?, ?, ?)
                """, (qid, rel_path, order_idx))
                qi_inserted += 1

        # Atualizar stem na tabela questions
        cur.execute("UPDATE questions SET stem = ? WHERE id = ?", (clean_stem, qid))
        stems_updated += 1

    print(f"  -> {qi_inserted} registros inseridos em question_images.")
    print(f"  -> {stems_updated} enunciados limpos na tabela questions.")

    # 5.2 Atualizar explicações
    print("2/3 Atualizando referências em explanations...")
    exps_updated = 0

    exp_by_qid = {}
    for item in exp_tasks:
        qid = item[0]
        exp_by_qid.setdefault(qid, []).append(item)

    for qid, tasks in exp_by_qid.items():
        exp_row = cur.execute("SELECT explanation_text FROM explanations WHERE question_id = ?", (qid,)).fetchone()
        if not exp_row or not exp_row['explanation_text']:
            continue

        txt = exp_row['explanation_text']
        modified = False

        for t in tasks:
            url = t[2]
            rel_path = url_to_rel_path.get(url)
            if rel_path:
                local_api_url = f"/api/images/{rel_path}"
                if url in txt:
                    txt = txt.replace(url, local_api_url)
                    modified = True

        if modified:
            cur.execute("UPDATE explanations SET explanation_text = ? WHERE question_id = ?", (txt, qid))
            exps_updated += 1

    print(f"  -> {exps_updated} comentários de explicações atualizados com URLs locais /api/images/.")

    # 5.3 Atualizar questions_fts
    print("3/3 Reindexando FTS (questions_fts)...")
    try:
        cur.execute("DELETE FROM questions_fts")
        cur.execute("""
            INSERT INTO questions_fts (rowid, stem, explanation)
            SELECT q.id, q.stem, e.explanation_text
            FROM questions q
            LEFT JOIN explanations e ON q.id = e.question_id
        """)
        print("  -> questions_fts reindexado com sucesso.")
    except Exception as e:
        print(f"  -> Aviso FTS: {e}")

    conn.commit()
    conn.close()

    print("\n" + "="*80)
    print("MIGRAÇÃO DE IMAGENS CONCLUÍDA COM SUCESSO!")
    print("="*80)

if __name__ == "__main__":
    main()
