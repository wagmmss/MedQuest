"""
Extrai questões, alternativas, gabarito e imagens dos PDFs exportados da EstratégiaMed
e popula o banco de dados SQLite usado pelo app de estudo.

Uso:
    python extract.py
"""
import hashlib
import os
import re
import shutil
import sqlite3
from collections import Counter
from datetime import datetime

import fitz  # PyMuPDF
import pdfplumber

import glob

SRC_DIR = os.environ.get("MEDQUEST_PDF_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")

# Encontra dinamicamente todos os PDFs no SRC_DIR
pdf_paths = glob.glob(os.path.join(SRC_DIR, "*.pdf"))
SOURCE_FILES = [(os.path.basename(p), os.path.splitext(os.path.basename(p))[0]) for p in pdf_paths]

# --- correção de ligaduras quebradas (fontes embutidas no export) ---
CID_MAP = {
    42: "fl", 66: "fi", 67: "fl", 74: "fi", 78: "fl", 83: "fl",
    2: "l", 111: "f",
}
CID_RE = re.compile(r"\(cid:(\d+)\)")


def fix_cid(text: str) -> str:
    def repl(m):
        code = int(m.group(1))
        return CID_MAP.get(code, "")
    return CID_RE.sub(repl, text)


# frases de tag conhecidas (para limpar a "tema" residual, best-effort)
KNOWN_TAG_PATTERNS = [
    r"Hospital de Reabilita[cç][aã]o de Anomalias Craniofaciais\s*-?\s*HRAC\s*USP",
    r"Universidade de S[aã]o Paulo\s*-\s*USP\s*-\s*SP\s*\(Hospital das Cl[ií]nicas da Faculdade de Medicina da USP\s*-\s*HC\)",
    r"Universidade de S[aã]o Paulo\s*-\s*USP\s*-\s*RP\s*\(Hospital das Cl[ií]nicas da Faculdade de Medicina de Ribeir[aã]o Preto da USP\)",
    r"Universidade Federal de S[aã]o Paulo\s*-\s*UNIFESP\s*\(Hospital Universit[aá]rio da UNIFESP\)",
    r"Universidade Estadual de Campinas\s*-\s*Unicamp\s*\(Faculdade de Ci[eê]ncias M[eé]dicas da Unicamp\s*-\s*FCM\)\s*\(Hospital de Cl[ií]nicas da Unicamp\)",
    r"Resid[eê]ncia \(Acesso Direto\)",
    r"Resid[eê]ncia com pr[eé]-requisito - Cirurgia \(R\+ CIR\)",
    r"N[aã]o se aplica",
    r"P[uú]blico - Estadual",
    r"Privado",
    r"Acesso Direto \(R\d\)",
    r"\bR\d\b",
    r"\d+\s*anos?\b",
    r"\bSP\s*-\s*",
]
KNOWN_TAG_RE = re.compile("|".join(KNOWN_TAG_PATTERNS))


def classify_institution(tag_zone: str):
    if "Hospital de Reabilitação de Anomalias Craniofaciais" in tag_zone or "HRAC" in tag_zone:
        return "HRAC-USP", "USP - Hospital de Reabilitação de Anomalias Craniofaciais (HRAC), Bauru"
    if "Ribeirão Preto" in tag_zone:
        return "USP-RP", "USP - Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto (HCRP)"
    if "Faculdade de Medicina da USP" in tag_zone or "USP - SP" in tag_zone:
        return "USP-SP", "USP - Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP)"
    if "USP" in tag_zone:
        return "USP-outro", "USP (campus não identificado)"
    if "Campinas" in tag_zone or "Unicamp" in tag_zone:
        return "UNICAMP", "UNICAMP - Hospital de Clínicas da Unicamp (FCM-Unicamp)"
    if "UNIFESP" in tag_zone:
        return "UNIFESP", "UNIFESP - Hospital Universitário da UNIFESP"
    return "OUTRO", "Instituição não identificada"


def extract_year(tag_zone: str):
    years = re.findall(r"\b(20[12]\d)\b", tag_zone)
    if not years:
        return None
    return int(Counter(years).most_common(1)[0][0])


def extract_topic(tag_zone: str) -> str:
    t = KNOWN_TAG_RE.sub(" ", tag_zone)
    t = re.sub(r"\b20[12]\d\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -\n")
    return t


def build_lines_for_page(page):
    """Agrupa palavras da página em linhas usando a coordenada 'top', e marca
    cada linha como tag (fonte Bold, badges de instituição/ano/especialidade)
    ou conteúdo (fonte Light, enunciado/alternativas) com base na fonte
    predominante da linha. Essa distinção tipográfica é muito mais confiável
    do que heurísticas de texto, pois as tags aparecem em ordem embaralhada
    (wrap de badges) e às vezes vêm acompanhadas de ruído de painel de filtro
    que vaza para o PDF exportado -- mas ambos sempre usam a fonte Bold."""
    words = page.extract_words(extra_attrs=["size", "fontname"])
    lines = []
    cur = []
    cur_top = None
    for w in words:
        if cur_top is None or abs(w["top"] - cur_top) > 2:
            if cur:
                lines.append(cur)
            cur = [w]
            cur_top = w["top"]
        else:
            cur.append(w)
            cur_top = w["top"]
    if cur:
        lines.append(cur)

    out = []
    for line_words in lines:
        text = " ".join(w["text"] for w in line_words)
        n_bold = sum(1 for w in line_words if "Bold" in w["fontname"])
        is_bold = n_bold >= len(line_words) / 2
        top = min(w["top"] for w in line_words)
        out.append({"text": text, "is_bold": is_bold, "top": top})
    return out


def find_alt_sequence_lines(content_lines):
    """As alternativas aparecem no PDF como uma linha contendo só a letra
    (A/B/C/D/E), seguida por uma ou mais linhas com o texto da opção. Aqui
    localizamos a sequência real A,B,C,D[,E] entre as linhas de conteúdo."""
    markers = [(i, l["text"].strip()) for i, l in enumerate(content_lines)
               if l["text"].strip() in ("A", "B", "C", "D", "E")]
    n = len(markers)
    for i in range(n):
        if markers[i][1] != "A":
            continue
        seq = [markers[i]]
        expected = ord("B")
        j = i + 1
        while j < n and markers[j][1] == chr(expected):
            seq.append(markers[j])
            expected += 1
            j += 1
        if len(seq) >= 4:
            return seq
    return None


def split_alternatives_lines(content_lines, seq):
    alts = {}
    for k, (line_idx, letter) in enumerate(seq):
        start = line_idx + 1
        end = seq[k + 1][0] if k + 1 < len(seq) else len(content_lines)
        text = " ".join(l["text"] for l in content_lines[start:end]).strip()
        text = re.sub(r"\s+", " ", text)
        alts[letter] = text
    return alts


COMMENT_RE = re.compile(r"Essa quest[aã]o possui coment[aá]rio do professor no site\s*(\d+)?")


def parse_pdf(path, source_label):
    print(f"--- Parsing {source_label} ---")

    # 1) todas as linhas do documento, em ordem, com página e se é "tag" (Bold) ou "conteúdo" (Light)
    global_lines = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages):
            for pl in build_lines_for_page(page):
                pl["page"] = pno
                global_lines.append(pl)

    for gl in global_lines:
        gl["text"] = fix_cid(gl["text"])

    # 2) posições das marcações "Questão N" e da seção "Respostas:"
    q_positions = []
    resp_idx = None
    for idx, gl in enumerate(global_lines):
        t = gl["text"].strip()
        m = re.match(r"^Quest[aã]o\s+(\d+)", t)
        if m:
            q_positions.append((idx, int(m.group(1))))
        elif t.startswith("Respostas:") and resp_idx is None:
            resp_idx = idx

    end_of_questions = resp_idx if resp_idx is not None else len(global_lines)

    # 3) gabarito (a partir da seção "Respostas:")
    answers = {}
    if resp_idx is not None:
        resp_text = " ".join(gl["text"] for gl in global_lines[resp_idx:])
        for m in re.finditer(r"(\d+)\s+([A-E])\b", resp_text):
            answers[int(m.group(1))] = m.group(2)

    # 4) monta cada questão a partir do intervalo de linhas entre marcadores
    records = []
    anchors = []  # (page, top, source_number) -- início de cada questão, para associar imagens
    for k, (idx, qnum) in enumerate(q_positions):
        start = idx + 1
        end = q_positions[k + 1][0] if k + 1 < len(q_positions) else end_of_questions
        block_lines = global_lines[start:end]
        if not block_lines:
            continue
        anchors.append((global_lines[idx]["page"], global_lines[idx]["top"], qnum))

        tag_lines = [l for l in block_lines if l["is_bold"]]
        content_lines = [l for l in block_lines if not l["is_bold"]]

        tag_zone = "\n".join(l["text"] for l in tag_lines)

        # remove a linha de rodapé "Essa questão possui comentário..." (e tudo depois)
        comment_code = None
        for ci, l in enumerate(content_lines):
            cm = COMMENT_RE.search(l["text"])
            if cm:
                comment_code = cm.group(1) if cm.group(1) else None
                content_lines = content_lines[:ci]
                break

        inst_code, inst_label = classify_institution(tag_zone)
        year = extract_year(tag_zone)
        topic = extract_topic(tag_zone)

        seq = find_alt_sequence_lines(content_lines)
        if seq:
            stem = " ".join(l["text"] for l in content_lines[: seq[0][0]]).strip()
            stem = re.sub(r"\s+", " ", stem)
            alts = split_alternatives_lines(content_lines, seq)
        else:
            stem = " ".join(l["text"] for l in content_lines).strip()
            stem = re.sub(r"\s+", " ", stem)
            alts = {}

        missing_alts = (not alts) or any(not v for v in alts.values())

        page_start = block_lines[0]["page"]
        page_end = block_lines[-1]["page"]
        correct_letter = answers.get(qnum)

        records.append({
            "source_number": qnum,
            "year": year,
            "institution_code": inst_code,
            "institution_label": inst_label,
            "topic": topic,
            "stem": stem,
            "alternatives": alts,
            "correct_letter": correct_letter,
            "missing_alts": missing_alts,
            "comment_code": comment_code,
            "page_start": page_start,
            "page_end": page_end,
        })

    print(f"    {len(records)} questões, {sum(1 for r in records if r['missing_alts'])} com alternativas ausentes, "
          f"{sum(1 for r in records if not r['correct_letter'])} sem gabarito encontrado")
    return records, anchors


def collect_image_candidates(path):
    """Coleta candidatas a imagem usando get_image_info do PyMuPDF."""
    doc = fitz.open(path)
    candidates = []
    for pno, page in enumerate(doc):
        imgs = page.get_image_info(xrefs=True)
        if not imgs:
            continue
        page_rect = page.rect
        page_w, page_h = page_rect.width, page_rect.height
        for img in imgs:
            xref = img.get("xref")
            if not xref:
                continue
            bbox = img["bbox"]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            # descarta de cara a arte de fundo que cobre quase a página inteira
            if w >= 0.85 * page_w and h >= 0.85 * page_h:
                continue
            try:
                base = doc.extract_image(xref)
            except Exception:
                continue
            data = base["image"]
            if len(data) < 2500:
                continue
            candidates.append({
                "page": pno,
                "top": bbox[1],
                "ext": base["ext"],
                "data": data,
            })
    doc.close()
    candidates.sort(key=lambda r: (r["page"], r["top"]))
    return candidates


def filter_decorative_and_save(candidates, source_slug, decorative_hashes):
    """Remove candidatas cujo hash de conteúdo é um dos identificados como
    decorativo/repetido (logo, marca d'água, textura de fundo) e grava o
    restante em disco. Retorna lista de dicts {page, top, file_path}."""
    out_subdir = os.path.join(IMG_DIR, source_slug)
    os.makedirs(out_subdir, exist_ok=True)
    results = []
    counters = {}
    for c in candidates:
        h = hashlib.md5(c["data"]).hexdigest()
        if h in decorative_hashes:
            continue
        pno = c["page"]
        idx = counters.get(pno, 0)
        counters[pno] = idx + 1
        fname = f"p{pno + 1:04d}_{idx}.{c['ext']}"
        fpath = os.path.join(out_subdir, fname)
        with open(fpath, "wb") as f:
            f.write(c["data"])
        results.append({"page": pno, "top": c["top"], "file_path": f"images/{source_slug}/{fname}"})
    return results


def assign_images_to_questions(anchors, images):
    """Para cada imagem (page, top), encontra a última âncora de questão
    (page, top, source_number) que a precede na ordem de leitura do documento
    (merge de duas listas já ordenadas), e associa a imagem a essa questão."""
    anchors_sorted = sorted(anchors, key=lambda a: (a[0], a[1]))
    assigned = {}
    if not anchors_sorted:
        return assigned
    ai = 0
    for img in images:
        key = (img["page"], img["top"])
        while ai + 1 < len(anchors_sorted) and (anchors_sorted[ai + 1][0], anchors_sorted[ai + 1][1]) <= key:
            ai += 1
        qnum = anchors_sorted[ai][2]
        assigned.setdefault(qnum, []).append(img["file_path"])
    return assigned


def build_db(all_records_by_source):
    if not os.path.exists(DB_PATH):
        print(f"Criando novo banco de dados em {DB_PATH}")
    else:
        print(f"Banco existente {DB_PATH}. Usando UPSERT/INSERT IGNORE para preservar dados do usuário.")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT NOT NULL,
        source_number INTEGER NOT NULL,
        year INTEGER,
        institution_code TEXT,
        institution_label TEXT,
        topic TEXT,
        stem TEXT,
        correct_letter TEXT,
        missing_alts INTEGER,
        comment_code TEXT,
        page_start INTEGER,
        page_end INTEGER
    );
    CREATE TABLE IF NOT EXISTS alternatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL REFERENCES questions(id),
        letter TEXT NOT NULL,
        text TEXT,
        is_correct INTEGER
    );
    CREATE TABLE IF NOT EXISTS question_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL REFERENCES questions(id),
        file_path TEXT NOT NULL,
        order_index INTEGER
    );
    CREATE TABLE IF NOT EXISTS explanations (
        question_id INTEGER PRIMARY KEY REFERENCES questions(id),
        explanation_text TEXT,
        generated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL REFERENCES questions(id),
        selected_letter TEXT,
        is_correct INTEGER,
        answered_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_alt_qid ON alternatives(question_id);
    CREATE INDEX IF NOT EXISTS idx_img_qid ON question_images(question_id);
    CREATE INDEX IF NOT EXISTS idx_att_qid ON attempts(question_id);
    CREATE INDEX IF NOT EXISTS idx_q_inst ON questions(institution_code);
    CREATE INDEX IF NOT EXISTS idx_q_year ON questions(year);
    CREATE INDEX IF NOT EXISTS idx_q_source ON questions(source_file);
    """)

    for source_label, records, image_map in all_records_by_source:
        for r in records:
            # Evita duplicatas se já existe questão do mesmo arquivo/número
            cur.execute("SELECT id FROM questions WHERE source_file = ? AND source_number = ?", 
                        (source_label, r["source_number"]))
            existing_q = cur.fetchone()
            
            if existing_q:
                qid = existing_q[0]
            else:
                cur.execute(
                    """INSERT INTO questions
                    (source_file, source_number, year, institution_code, institution_label,
                     topic, stem, correct_letter, missing_alts, comment_code, page_start, page_end)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (source_label, r["source_number"], r["year"], r["institution_code"],
                     r["institution_label"], r["topic"], r["stem"], r["correct_letter"],
                     1 if r["missing_alts"] else 0, r["comment_code"], r["page_start"], r["page_end"]),
                )
                qid = cur.lastrowid
                for letter, text in r["alternatives"].items():
                    cur.execute(
                        "INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?,?,?,?)",
                        (qid, letter, text, 1 if letter == r["correct_letter"] else 0),
                    )
            
            for order, fp in enumerate(image_map.get(r["source_number"], [])):
                # Delete existing image if it exists to avoid duplicates
                cur.execute("DELETE FROM question_images WHERE question_id = ? AND file_path = ?", (qid, fp))
                cur.execute(
                    "INSERT INTO question_images (question_id, file_path, order_index) VALUES (?,?,?)",
                    (qid, fp, order),
                )

    conn.commit()
    conn.close()


DECORATIVE_REPEAT_THRESHOLD = 3  # imagem com mais repetições idênticas que isso é considerada decorativa


def main():
    parsed = []  # (label, slug, records, anchors, candidates)
    hash_counts = Counter()

    for fname, label in SOURCE_FILES:
        path = os.path.join(SRC_DIR, fname)
        slug = re.sub(r"[^a-zA-Z]", "", label.split()[0]).lower()
        records, anchors = parse_pdf(path, label)
        print(f"    coletando candidatas a imagem de {fname}...")
        candidates = collect_image_candidates(path)
        for c in candidates:
            hash_counts[hashlib.md5(c["data"]).hexdigest()] += 1
        print(f"    {len(candidates)} candidatas")
        parsed.append((label, slug, records, anchors, candidates))

    decorative_hashes = {h for h, n in hash_counts.items() if n > DECORATIVE_REPEAT_THRESHOLD}
    print(f"--- {len(decorative_hashes)} imagens identificadas como decorativas/repetidas (excluídas) ---")

    all_data = []
    for label, slug, records, anchors, candidates in parsed:
        images = filter_decorative_and_save(candidates, slug, decorative_hashes)
        image_map = assign_images_to_questions(anchors, images)
        n_assigned = sum(len(v) for v in image_map.values())
        print(f"    {label}: {len(images)} imagens de conteúdo reais, {n_assigned} associadas a questões")
        all_data.append((label, records, image_map))

    print("--- Gravando banco de dados ---")
    build_db(all_data)
    print(f"OK -> {DB_PATH}")


if __name__ == "__main__":
    main()
