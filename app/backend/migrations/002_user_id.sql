-- Migration 002: user_id (preparação para multiusuário, lançando só p/ 1 usuário).
-- Additivo e retrocompatível: default 1 mantém o código atual funcionando.
ALTER TABLE attempts          ADD COLUMN user_id INTEGER DEFAULT 1;
ALTER TABLE spaced_repetition ADD COLUMN user_id INTEGER DEFAULT 1;
ALTER TABLE favorites         ADD COLUMN user_id INTEGER DEFAULT 1;
ALTER TABLE planner_progress  ADD COLUMN user_id INTEGER DEFAULT 1;
ALTER TABLE planner_config    ADD COLUMN user_id INTEGER DEFAULT 1;
