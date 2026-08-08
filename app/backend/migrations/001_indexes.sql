-- Migration 001: índices de performance
-- Aplicar DEPOIS que a reclassificação de subtemas terminar (evita lock).
-- Rodar no DataGrip (console SQL) ou: sqlite3 medquest.db < migrations/001_indexes.sql

CREATE INDEX IF NOT EXISTS idx_attempts_qid   ON attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_attempts_when  ON attempts(answered_at);
CREATE INDEX IF NOT EXISTS idx_q_area_sub     ON questions(area, subtema);
CREATE INDEX IF NOT EXISTS idx_q_year_inst    ON questions(year, institution_code);
CREATE INDEX IF NOT EXISTS idx_q_missing      ON questions(missing_alts);
CREATE INDEX IF NOT EXISTS idx_srs_due        ON spaced_repetition(next_review_date);
CREATE INDEX IF NOT EXISTS idx_imgs_qid       ON question_images(question_id);

-- Atualiza estatísticas do otimizador
ANALYZE;
