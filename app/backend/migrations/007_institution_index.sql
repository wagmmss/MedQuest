-- Migration 007: Composite index on institution_code and institution_label
CREATE INDEX IF NOT EXISTS idx_questions_inst_code_label ON questions (institution_code, institution_label);
