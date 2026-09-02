"""Parser e importador seguro para pacotes e arquivos de exportação do Anki (.apkg, .colpkg, .txt)."""

import html
import io
import json
import logging
import os
import re
import sqlite3
import tempfile
import zipfile
from typing import Any

logger = logging.getLogger(__name__)


def clean_anki_html(text: str) -> str:
    """Converte HTML exportado do Anki para texto limpo e legível mantendo quebras de linha e destaques."""
    if not text:
        return ""

    # Normaliza entidades HTML básicas
    s = text

    # Remove comentários HTML
    s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)

    # Converte quebras de linha HTML comuns
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</div>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</li>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<li[^>]*>", "• ", s, flags=re.IGNORECASE)

    # Converte estilos de formatação essenciais
    s = re.sub(r"<b\b[^>]*>(.*?)</b>", r"**\1**", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<strong\b[^>]*>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<i\b[^>]*>(.*?)</i>", r"*\1*", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<em\b[^>]*>(.*?)</em>", r"*\1*", s, flags=re.DOTALL | re.IGNORECASE)

    # Remove tags HTML restantes
    s = re.sub(r"<[^>]+>", "", s)

    # Decodifica entidades HTML como &nbsp;, &lt;, &gt;, &amp;
    s = html.unescape(s)
    s = s.replace("\xa0", " ")

    # Normaliza linhas em branco excessivas
    s = re.sub(r"\r\n|\r", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def parse_anki_tags(tags_str: str) -> list[str]:
    """Converte string de tags do Anki (ex: 'tag1 tag2 tag::subtag') em lista limpa."""
    if not tags_str:
        return []
    raw_tags = tags_str.strip().split()
    clean_tags = []
    for t in raw_tags:
        cleaned = t.strip()
        if cleaned and cleaned not in clean_tags:
            clean_tags.append(cleaned)
    return clean_tags


def parse_apkg_bytes(file_bytes: bytes, fallback_deck_name: str = "Anki") -> list[dict[str, Any]]:
    """Extrai notas e baralhos de um arquivo .apkg ou .colpkg em formato ZIP."""
    cards_out: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_zip_path = os.path.join(temp_dir, "anki_package.zip")
        with open(temp_zip_path, "wb") as f:
            f.write(file_bytes)

        if not zipfile.is_zipfile(temp_zip_path):
            raise ValueError("O arquivo enviado não é um pacote ZIP/APKG válido.")

        with zipfile.ZipFile(temp_zip_path, "r") as z:
            namelist = z.namelist()
            # O banco Anki pode ser collection.anki2 ou collection.anki21
            db_name = None
            if "collection.anki2" in namelist:
                db_name = "collection.anki2"
            elif "collection.anki21" in namelist:
                db_name = "collection.anki21"
            elif "collection.anki21b" in namelist:
                db_name = "collection.anki21b"

            if not db_name:
                raise ValueError("Nenhum banco de dados do Anki (collection.anki2) foi encontrado no arquivo .apkg.")

            z.extract(db_name, temp_dir)
            extracted_db_path = os.path.join(temp_dir, db_name)

            conn = sqlite3.connect(extracted_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                # 1. Carrega os baralhos e modelos da tabela 'col'
                deck_map: dict[int, str] = {}
                model_map: dict[int, dict[str, Any]] = {}

                col_row = cursor.execute("SELECT decks, models FROM col").fetchone()
                if col_row:
                    try:
                        decks_data = json.loads(col_row["decks"]) if col_row["decks"] else {}
                        for did_str, dinfo in decks_data.items():
                            try:
                                did = int(did_str)
                                deck_map[did] = dinfo.get("name", fallback_deck_name)
                            except (ValueError, TypeError):
                                pass
                    except Exception as e:
                        logger.warning("Falha ao analisar decks do col: %s", e)

                    try:
                        models_data = json.loads(col_row["models"]) if col_row["models"] else {}
                        for mid_str, minfo in models_data.items():
                            try:
                                mid = int(mid_str)
                                model_map[mid] = minfo
                            except (ValueError, TypeError):
                                pass
                    except Exception as e:
                        logger.warning("Falha ao analisar models do col: %s", e)

                # 2. Mapeia cada note ID (nid) para seu deck ID (did) através da tabela 'cards'
                note_to_deck: dict[int, int] = {}
                card_rows = cursor.execute("SELECT nid, did FROM cards ORDER BY id ASC").fetchall()
                for c in card_rows:
                    if c["nid"] not in note_to_deck:
                        note_to_deck[c["nid"]] = c["did"]

                # 3. Lê as notas da tabela 'notes'
                notes_rows = cursor.execute("SELECT id, mid, flds, tags FROM notes ORDER BY id ASC").fetchall()

                for n in notes_rows:
                    nid = n["id"]
                    mid = n["mid"]
                    flds_raw = n["flds"] or ""
                    tags_raw = n["tags"] or ""

                    fields = [clean_anki_html(f) for f in flds_raw.split("\x1f")]
                    if not fields or not any(fields):
                        continue

                    # Determina o baralho associado
                    did = note_to_deck.get(nid, 1)
                    deck_name = deck_map.get(did, fallback_deck_name)
                    if not deck_name or deck_name == "Default":
                        deck_name = fallback_deck_name

                    tags = parse_anki_tags(tags_raw)

                    # Determina Frente e Verso
                    front = fields[0] if len(fields) > 0 else ""
                    back = ""
                    if len(fields) > 1:
                        back = "\n\n".join(f for f in fields[1:] if f.strip())

                    # Se a frente for vazia, pula
                    if not front.strip():
                        continue

                    cards_out.append({
                        "front": front,
                        "back": back,
                        "deck_name": deck_name,
                        "tags": tags,
                        "source_context": f"Anki: {deck_name}",
                        "source_type": "anki_apkg",
                        "anki_nid": nid,
                    })

            finally:
                conn.close()

    return cards_out


def parse_anki_text(text_content: str, default_deck_name: str = "Anki") -> list[dict[str, Any]]:
    """Analisa arquivo de texto exportado pelo Anki (.txt, .tsv, .csv com headers #separator, #deck, etc.)."""
    lines = text_content.splitlines()
    cards_out: list[dict[str, Any]] = []

    separator = "\t"
    deck_name = default_deck_name
    is_html = True
    tags_col = -1

    data_lines = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        if line_clean.startswith("#"):
            lower = line_clean.lower()
            if lower.startswith("#separator:"):
                sep_val = line_clean.split(":", 1)[1].strip()
                if sep_val.lower() == "tab":
                    separator = "\t"
                elif sep_val.lower() == "comma":
                    separator = ","
                elif sep_val.lower() == "semicolon":
                    separator = ";"
                elif sep_val.lower() == "space":
                    separator = " "
                else:
                    separator = sep_val
            elif lower.startswith("#deck:"):
                deck_val = line_clean.split(":", 1)[1].strip()
                if deck_val:
                    deck_name = deck_val
            elif lower.startswith("#html:"):
                is_html = line_clean.split(":", 1)[1].strip().lower() == "true"
            elif lower.startswith("#tags column:"):
                try:
                    tags_col = int(line_clean.split(":", 1)[1].strip()) - 1  # 1-based index no Anki
                except ValueError:
                    pass
            continue

        data_lines.append(line)

    for line in data_lines:
        parts = line.split(separator)
        if not parts:
            continue

        tags: list[str] = []
        if tags_col >= 0 and tags_col < len(parts):
            tags_raw = parts.pop(tags_col)
            tags = parse_anki_tags(tags_raw)

        if not parts:
            continue

        front_raw = parts[0]
        back_parts = parts[1:]

        front = clean_anki_html(front_raw) if is_html else front_raw.strip()
        back = "\n\n".join(
            clean_anki_html(p) if is_html else p.strip()
            for p in back_parts if p.strip()
        )

        if not front:
            continue

        cards_out.append({
            "front": front,
            "back": back,
            "deck_name": deck_name,
            "tags": tags,
            "source_context": f"Anki: {deck_name}",
            "source_type": "anki_txt",
            "anki_nid": None,
        })

    return cards_out
