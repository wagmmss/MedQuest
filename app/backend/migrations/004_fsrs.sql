-- Migration 004: estado do FSRS por questão (substitui o SM-2 simplificado).
-- O init_db() também garante esta coluna; este arquivo documenta a mudança.
ALTER TABLE spaced_repetition ADD COLUMN fsrs_card TEXT;
