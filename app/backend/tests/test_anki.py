"""Testes unitários e de integração para a funcionalidade de importação e estudo do Anki."""

import io
import json
import sqlite3
import tempfile
import zipfile

from api.anki import clean_anki_html, parse_anki_tags, parse_anki_text, parse_apkg_bytes


def _create_synthetic_apkg() -> bytes:
    """Gera um arquivo .apkg sintético válido em memória com baralhos e notas."""
    with tempfile.TemporaryDirectory() as td:
        db_path = f"{td}/collection.anki2"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Cria tabelas essenciais do Anki
        cur.execute("""
            CREATE TABLE col (
                id integer primary key,
                crt integer not null,
                mod integer not null,
                scm integer not null,
                ver integer not null,
                dty integer not null,
                usn integer not null,
                ls integer not null,
                conf text not null,
                models text not null,
                decks text not null,
                dconf text not null,
                tags text not null
            )
        """)
        cur.execute("""
            CREATE TABLE notes (
                id integer primary key,
                guid text not null,
                mid integer not null,
                mod integer not null,
                usn integer not null,
                tags text not null,
                flds text not null,
                sfld text not null,
                csum integer not null,
                flags integer not null,
                data text not null
            )
        """)
        cur.execute("""
            CREATE TABLE cards (
                id integer primary key,
                nid integer not null,
                did integer not null,
                ord integer not null,
                mod integer not null,
                usn integer not null,
                type integer not null,
                queue integer not null,
                due integer not null,
                ivl integer not null,
                factor integer not null,
                reps integer not null,
                lapses integer not null,
                left integer not null,
                odue integer not null,
                odid integer not null,
                flags integer not null,
                data text not null
            )
        """)

        decks_json = json.dumps({
            "1": {"id": 1, "name": "Default"},
            "1500000000000": {"id": 1500000000000, "name": "Cardiologia::Arritmias"},
        })
        models_json = json.dumps({
            "1600000000000": {
                "id": 1600000000000,
                "name": "Cloze",
                "flds": [{"name": "Text", "ord": 0}, {"name": "Extra", "ord": 1}],
            }
        })

        cur.execute(
            "INSERT INTO col VALUES (1, 1600000000, 1600000000, 1600000000, 11, 0, 0, 0, '{}', ?, ?, '{}', '{}')",
            (models_json, decks_json),
        )

        # Inserção de notas
        # Note 1: Cloze no baralho de Cardiologia
        flds_1 = "A tríade de Beck consiste em {{c1::hipotensão}}, {{c1::estase jugular}} e {{c1::hipofonese de bulhas}}.\x1fPatognomônico de tamponamento cardíaco."
        cur.execute(
            "INSERT INTO notes VALUES (101, 'guid1', 1600000000000, 1600000000, 0, ' #cardio #emergencia ', ?, 'sfld', 0, 0, '')",
            (flds_1,),
        )
        cur.execute(
            "INSERT INTO cards VALUES (201, 101, 1500000000000, 0, 1600000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '')"
        )

        # Note 2: Básico com HTML
        flds_2 = "<b>Qual o tratamento inicial do choque anafilático?</b>\x1f<i>Adrenalina</i> IM 0,5mg na coxa."
        cur.execute(
            "INSERT INTO notes VALUES (102, 'guid2', 1600000000000, 1600000000, 0, ' #emergencia ', ?, 'sfld', 0, 0, '')",
            (flds_2,),
        )
        cur.execute(
            "INSERT INTO cards VALUES (202, 102, 1500000000000, 0, 1600000000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '')"
        )

        conn.commit()
        conn.close()

        # Cria o arquivo ZIP (.apkg)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, "collection.anki2")
            zf.writestr("media", "{}")

        return zip_buffer.getvalue()


def test_clean_anki_html():
    html_input = "<div><b>Sintoma principal:</b><br>• Dor precordial<br />• Sudorese&nbsp;&amp;&nbsp;dispneia</div>"
    cleaned = clean_anki_html(html_input)
    assert "**Sintoma principal:**" in cleaned
    assert "• Dor precordial" in cleaned
    assert "Sudorese & dispneia" in cleaned


def test_parse_anki_text():
    raw_text = """#separator:tab
#html:true
#tags column:3
#deck:Medicina::Infectologia
Qual a droga de escolha para Neurotoxoplasmose?\tSulfadiazina + Pirimetamina + Ácido Folínico\tHIV Imunossupressão
O sinal de Romaña é típico de {{c1::Doença de Chagas}}.\tTripanossomíase americana\tParasitologia
"""
    cards = parse_anki_text(raw_text)
    assert len(cards) == 2
    assert cards[0]["deck_name"] == "Medicina::Infectologia"
    assert "Sulfadiazina" in cards[0]["back"]
    assert "HIV" in cards[0]["tags"]
    assert "{{c1::Doença de Chagas}}" in cards[1]["front"]


def test_parse_apkg_bytes():
    apkg_bytes = _create_synthetic_apkg()
    cards = parse_apkg_bytes(apkg_bytes)
    assert len(cards) == 2
    card_beck = next(c for c in cards if "tríade de Beck" in c["front"])
    assert card_beck["deck_name"] == "Cardiologia::Arritmias"
    assert "#cardio" in card_beck["tags"]
    assert card_beck["anki_nid"] == 101


def test_anki_endpoints_flow(client):
    # 1. Importa via arquivo de texto
    tsv_content = "O que avalia a escala de Glasgow?\tNível de consciência\tNeurologia Trauma"
    data = {
        "file": (io.BytesIO(tsv_content.encode("utf-8")), "neuro.txt"),
        "deck_name": "Neurologia",
    }
    r_import = client.post("/api/flashcards/import/file", data=data, content_type="multipart/form-data")
    assert r_import.status_code == 200
    res = r_import.get_json()
    assert res["success"] is True
    assert res["total_imported"] == 1

    # 2. Importa via pacote .apkg sintético
    apkg_bytes = _create_synthetic_apkg()
    data_apkg = {
        "file": (io.BytesIO(apkg_bytes), "cardio.apkg"),
    }
    r_apkg = client.post("/api/flashcards/import/file", data=data_apkg, content_type="multipart/form-data")
    assert r_apkg.status_code == 200
    res_apkg = r_apkg.get_json()
    assert res_apkg["success"] is True
    assert res_apkg["total_imported"] == 2

    # 3. Lista baralhos e verifica contagens
    r_decks = client.get("/api/flashcards/decks")
    assert r_decks.status_code == 200
    decks_data = r_decks.get_json()
    deck_names = [d["name"] for d in decks_data["decks"]]
    assert "Neurologia" in deck_names
    assert "Cardiologia::Arritmias" in deck_names

    # 4. Consulta fila de revisão filtrando por baralho
    r_due_neuro = client.get("/api/flashcards/review?deck=Neurologia")
    assert r_due_neuro.status_code == 200
    neuro_cards = r_due_neuro.get_json()
    assert len(neuro_cards) == 1
    assert neuro_cards[0]["deck_name"] == "Neurologia"
    assert "Glasgow" in neuro_cards[0]["front"]

    # 5. Importa lote via JSON (simulando AnkiConnect)
    r_batch = client.post("/api/flashcards/import/batch", json={
        "deck_name": "Pediatria",
        "cards": [
            {
                "front": "Qual o agente etiológico do Crupe Viral?",
                "back": "Vírus Parainfluenza",
                "tags": ["pediatria", "respiratorio"],
                "anki_nid": 99991,
            }
        ]
    })
    assert r_batch.status_code == 200
    assert r_batch.get_json()["total_imported"] == 1

    # 6. Revisa o cartão importado do Anki com FSRS
    fid = neuro_cards[0]["id"]
    r_review = client.post(f"/api/flashcards/{fid}/review", json={"confidence": "certeza"})
    assert r_review.status_code == 200

    # 7. Exclui um baralho importado
    r_del = client.delete("/api/flashcards/deck", json={"deck_name": "Neurologia"})
    assert r_del.status_code == 200
    assert r_del.get_json()["deleted_count"] == 1

    # Confirma que Neurologia não aparece mais
    r_decks_after = client.get("/api/flashcards/decks")
    deck_names_after = [d["name"] for d in r_decks_after.get_json()["decks"]]
    assert "Neurologia" not in deck_names_after
