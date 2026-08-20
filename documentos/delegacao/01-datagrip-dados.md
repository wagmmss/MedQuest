# Delegação → DataGrip (Fase 1: Dados)

**Objetivo:** limpar e indexar o banco. Executar tudo no DataGrip conectado a `app/backend/medquest.db`.
**Pré-requisito:** a reclassificação de subtemas precisa ter terminado (checar que `subtema_orig` existe e que cada área tem ~25-40 subtemas distintos).

> ⚠️ Faça backup antes de qualquer UPDATE/DELETE: `python app/backend/backup_db.py` (ou copie o `.db`).

---

## 1. Índices (impacto imediato de performance)
Rode o arquivo `app/backend/migrations/001_indexes.sql` (botão direito → Run, ou cole no console). Depois confirme:
```sql
SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';
```

## 2. Diagnóstico dos dados sujos
```sql
-- Instituições não identificadas (115 esperadas)
SELECT year, source_file, COUNT(*) FROM questions
WHERE institution_label LIKE '%o identificada%' GROUP BY year, source_file ORDER BY 3 DESC;

-- Questões com alternativas faltando (51 esperadas)
SELECT id, year, source_file, area FROM questions WHERE missing_alts = 1 ORDER BY year;

-- Sem explicação (poucas esperadas)
SELECT id, year, area FROM questions
WHERE missing_alts = 0 AND id NOT IN
  (SELECT question_id FROM explanations WHERE explanation_text IS NOT NULL AND explanation_text != '');
```

## 3. Limpeza
```sql
-- Instituição não identificada: são todas de 2021 (fontes misturadas), origem não recuperável.
-- Decisão recomendada: rótulo apresentável, sem perder o filtro por ano.
UPDATE questions SET institution_label = 'Outras provas 2021'
WHERE institution_label LIKE '%o identificada%';

-- missing_alts=1: não têm todas as alternativas; não entram no estudo.
-- Recomendado: deixar como está (o backend já filtra missing_alts=0). Só revisar à mão
-- as poucas que valha a pena consertar comparando com o PDF-fonte.
```

## 4. Busca full-text (FTS5) — destrava "buscar questão sobre X"
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
  stem, subtema, content='questions', content_rowid='id'
);
INSERT INTO questions_fts(rowid, stem, subtema)
  SELECT id, stem, subtema FROM questions;
-- Uso: SELECT id FROM questions_fts WHERE questions_fts MATCH 'apendicite';
```
(Depois adiciono no backend um endpoint `/api/v1/search?q=` que consulta essa tabela.)

## 5. Duplicatas (opcional)
```sql
-- Enunciados idênticos entre anos/instituições
SELECT substr(stem,1,80) AS ini, COUNT(*) n, GROUP_CONCAT(id) ids
FROM questions GROUP BY substr(stem,1,120) HAVING n > 1 ORDER BY n DESC;
```

## 6. Migração SQLite → Postgres (só quando for multiusuário — Fase 6)
DataGrip faz export nativo entre DBMS: botão direito na base → *Export Data to Database* → destino Postgres. Guardar para a Fase 6.

**Me devolva:** o resultado agregado das queries de diagnóstico (contagens), não as linhas.
