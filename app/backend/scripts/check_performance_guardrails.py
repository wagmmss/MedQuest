"""Script de Verificação Automatizada de Guardrails de Performance (CI/CD) — MedQuest.

Executa benchmark hermético rápido dos endpoints críticos e valida se estão dentro dos SLAs.
Garante isolamento completo sem depender de banco de produção, rede ou credenciais.
"""

from datetime import datetime, timedelta, timezone
import math
import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import create_app

GUARDRAILS = [
    {
        "name": "Busca FTS5 (/api/search)",
        "url": "/api/search?q=hipertensao&limit=10",
        "max_p95_ms": 30.0,
        "max_payload_kb": 50.0,
        "iterations": 25,
    },
    {
        "name": "Coverage Resumo (/api/coverage?summary_only=true)",
        "url": "/api/coverage?summary_only=true",
        # O endpoint agora evita materializar o detalhamento no modo resumo.
        # A margem preserva sensibilidade a regressões sem falhar por jitter de
        # scheduler/IO de runners compartilhados.
        "max_p95_ms": 15.0,
        "max_payload_kb": 5.0,
        "iterations": 25,
    },
    {
        "name": "Stats Overview (/api/stats/overview)",
        "url": "/api/stats/overview",
        "max_p95_ms": 5.0,
        "max_payload_kb": 5.0,
        "iterations": 25,
    },
    {
        "name": "Stats Timeline (/api/stats/timeline?days=14)",
        "url": "/api/stats/timeline?days=14",
        "max_p95_ms": 10.0,
        "max_payload_kb": 10.0,
        "iterations": 25,
    },
    {
        "name": "Stats Radar de Bancas (/api/stats/institution-radar)",
        "url": "/api/stats/institution-radar?institution=USP-SP&compare_institution=UNICAMP",
        "max_p95_ms": 15.0,
        "max_payload_kb": 10.0,
        "iterations": 25,
    },
]



def percentile(data, p):
    s = sorted(data)
    idx = max(0, math.ceil(len(s) * p) - 1)
    return round(s[idx], 2)


def seed_benchmark_db(db_path):
    """Inicializa e popula um banco de dados hermético representativo para o benchmark."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Tabelas core
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        source_file TEXT,
        source_number INTEGER,
        year INTEGER,
        institution_code TEXT,
        institution_label TEXT,
        topic TEXT,
        stem TEXT,
        correct_letter TEXT,
        missing_alts INTEGER DEFAULT 0,
        area TEXT,
        subtema TEXT,
        subtema_id TEXT,
        subtema_orig TEXT,
        editorial_status TEXT,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS alternatives (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        letter TEXT,
        text TEXT,
        is_correct INTEGER
    );

    CREATE TABLE IF NOT EXISTS explanations (
        question_id INTEGER PRIMARY KEY,
        explanation_text TEXT,
        generated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        selected_letter TEXT,
        is_correct INTEGER,
        answered_at TEXT,
        confidence TEXT,
        user_id TEXT DEFAULT '1',
        time_spent_ms INTEGER
    );

    CREATE TABLE IF NOT EXISTS favorites (
        question_id INTEGER,
        user_id TEXT DEFAULT '1',
        PRIMARY KEY (question_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS spaced_repetition (
        question_id INTEGER,
        efactor REAL,
        interval INTEGER,
        next_review_date TEXT,
        user_id TEXT DEFAULT '1',
        fsrs_card TEXT,
        PRIMARY KEY (question_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        front TEXT NOT NULL,
        back TEXT,
        created_at TEXT NOT NULL,
        next_review_date TEXT,
        fsrs_card TEXT,
        user_id TEXT DEFAULT '1',
        source_context TEXT,
        is_ai_generated INTEGER DEFAULT 0,
        report_status TEXT
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
        stem,
        explanation
    );
    """)

    # Seed de questões nas 5 grandes áreas médicas
    areas_seed = [
        ("Clínica Médica", "Hipertensão Arterial Sistêmica", "USP-SP", "USP", "Homem de 55 anos com hipertensão arterial estágio 2 e diabetes mellitus tipo 2."),
        ("Clínica Médica", "Hipertensão Arterial Sistêmica", "UNICAMP", "UNICAMP", "Mulher de 62 anos assintomática com níveis pressóricos de hipertensao mantidos em 160/100 mmHg."),
        ("Clínica Médica", "Diabetes Mellitus", "USP-RP", "USP RP", "Paciente com glicemia de jejum de 145 mg/dL e HbA1c de 7.8%."),
        ("Clínica Médica", "Insuficiência Cardíaca", "ENARE", "ENARE", "Paciente com dispneia aos esforços, fração de ejeção reduzida e sobrecarga volêmica."),
        ("Cirurgia", "Trauma e Atendimento Inicial", "USP-SP", "USP", "Vítima de colisão automobilística com hipotensão e dor abdominal à palpação."),
        ("Cirurgia", "Abdome Agudo", "UNICAMP", "UNICAMP", "Paciente com dor súbita em fossa ilíaca direita, febre e sinal de Blumberg positivo."),
        ("Cirurgia", "Hérnias da Parede Abdominal", "SUS-SP", "SUS-SP", "Paciente com abaulamento redutível em região inguinal direita."),
        ("Ginecologia e Obstetrícia", "Pré-Natal", "USP-SP", "USP", "Primigesta na 12ª semana de gestação realizando exames de rotina no pré-natal."),
        ("Ginecologia e Obstetrícia", "Hemorragias da Primeira Metade", "UNIFESP", "UNIFESP", "Gestante de 8 semanas com sangramento vaginal e cólica em hipogástrio."),
        ("Ginecologia e Obstetrícia", "Câncer de Colo Uterino", "ENARE", "ENARE", "Mulher de 35 anos com exame citopatológico apresentando lesão intraepitelial de alto grau."),
        ("Pediatria", "Imunização (PNI)", "USP-SP", "USP", "Lactente de 2 meses comparece para vacinação de rotina do calendário PNI."),
        ("Pediatria", "Crescimento e Desenvolvimento", "UNICAMP", "UNICAMP", "Criança de 1 ano com velocidade de crescimento abaixo do percentil 3."),
        ("Pediatria", "Aleitamento Materno", "USP-RP", "USP RP", "Recém-nascido em aleitamento materno exclusivo apresentando ganho de peso adequado."),
        ("Medicina Preventiva", "Epidemiologia", "USP-SP", "USP", "Estudo de coorte prospectivo avaliando a incidência de eventos cardiovasculares."),
        ("Medicina Preventiva", "Atenção Primária à Saúde", "ENARE", "ENARE", "Princípios da atenção primária e atributos essenciais de Starfield na Estratégia de Saúde da Família."),
        ("Medicina Preventiva", "Bioética", "SUS-SP", "SUS-SP", "Princípios da beneficência, não maleficência, autonomia e justiça na prática clínica."),
    ]

    qid = 1
    now_iso = datetime.now(timezone.utc).isoformat()

    for area, subtema, inst_code, inst_label, stem in areas_seed:
        cur.execute("""
            INSERT INTO questions (
                id, source_file, source_number, year, institution_code, institution_label,
                topic, stem, correct_letter, missing_alts, area, subtema, status
            ) VALUES (?, 'seed.json', ?, 2025, ?, ?, ?, ?, 'A', 0, ?, ?, 'active')
        """, (qid, qid, inst_code, inst_label, subtema, stem, area, subtema))

        # Alternativas
        cur.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, 'A', 'Conduta correta conforme diretriz.', 1)", (qid,))
        cur.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, 'B', 'Conduta incorreta / distrator.', 0)", (qid,))
        cur.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, 'C', 'Opção inadequada.', 0)", (qid,))
        cur.execute("INSERT INTO alternatives (question_id, letter, text, is_correct) VALUES (?, 'D', 'Opção contraindicada.', 0)", (qid,))

        # Explicação com Pulo do Gato
        explanation_text = f"**Gabarito**: Alternativa A.\n**Pulo do Gato**: Em {subtema}, a conduta de primeira linha é prioritária.\n**Raciocínio Clínico**: Revisão sistemática sobre {subtema}."
        cur.execute("INSERT INTO explanations (question_id, explanation_text, generated_at) VALUES (?, ?, ?)", (qid, explanation_text, now_iso))

        # FTS5 index
        cur.execute("INSERT INTO questions_fts (rowid, stem, explanation) VALUES (?, ?, ?)", (qid, stem, explanation_text))

        qid += 1

    # Seed de tentativas ao longo dos últimos 14 dias para user_id='1'
    base_time = datetime.now(timezone.utc)
    for day_offset in range(14):
        dt = (base_time - timedelta(days=day_offset)).isoformat()
        cur.execute("""
            INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at, confidence, user_id, time_spent_ms)
            VALUES (1, 'A', 1, ?, 'certeza', '1', 12500)
        """, (dt,))
        cur.execute("""
            INSERT INTO attempts (question_id, selected_letter, is_correct, answered_at, confidence, user_id, time_spent_ms)
            VALUES (2, 'B', 0, ?, 'duvida', '1', 18200)
        """, (dt,))

    con.commit()
    con.close()


def run_checks(guardrails=None):
    print("================================================================")
    print("[MEDQUEST CI] VERIFICACAO AUTOMATIZADA DE GUARDRAILS DE SLA")
    print("================================================================\n")

    # Garante execução hermética usando banco temporário isolado
    temp_fd, temp_db_path = tempfile.mkstemp(suffix="_guardrails_benchmark.db")
    os.close(temp_fd)

    old_db_env = os.environ.get("MEDQUEST_DB")
    os.environ["MEDQUEST_DB"] = temp_db_path

    active_guardrails = guardrails if guardrails is not None else GUARDRAILS

    try:
        seed_benchmark_db(temp_db_path)
        app = create_app(testing=True)
        client = app.test_client()

        failed = False

        for g in active_guardrails:

            name = g["name"]
            url = g["url"]
            max_p95 = g["max_p95_ms"]
            max_kb = g["max_payload_kb"]
            iters = g["iterations"]

            # Warmup e estabilização de GC
            import gc
            gc.collect()
            for _ in range(3):
                client.get(url)

            times = []
            payload_bytes = 0

            for _ in range(iters):
                t0 = time.perf_counter()
                res = client.get(url)
                t1 = time.perf_counter()
                if res.status_code != 200:
                    print(f"[FAIL] {name}: HTTP Status {res.status_code} inesperado.")
                    failed = True
                    break
                times.append((t1 - t0) * 1000)
                payload_bytes = len(res.data)

            if not times:
                continue

            p50 = percentile(times, 0.50)
            p95 = percentile(times, 0.95)
            kb = round(payload_bytes / 1024, 2)

            p95_ok = p95 <= max_p95
            payload_ok = kb <= max_kb

            status_str = "[PASS]" if (p95_ok and payload_ok) else "[FAIL]"
            print(f"{status_str} | {name}")
            print(f"       Latencia: P50={p50:.2f}ms | P95={p95:.2f}ms (Teto SLA: {max_p95:.1f}ms)")
            print(f"       Payload:  {kb:.2f} KB (Teto SLA: {max_kb:.1f} KB)\n")

            if not p95_ok or not payload_ok:
                failed = True

        if failed:
            print("[ERRO] Regressao de performance detectada! O build foi bloqueado.")
            return False
        else:
            print("[SUCESSO] Todos os endpoints estao dentro dos SLAs de performance.")
            return True

    finally:
        if old_db_env is not None:
            os.environ["MEDQUEST_DB"] = old_db_env
        else:
            os.environ.pop("MEDQUEST_DB", None)

        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError:
                pass


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
