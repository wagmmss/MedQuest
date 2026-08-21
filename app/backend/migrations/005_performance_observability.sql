CREATE INDEX IF NOT EXISTS idx_attempts_user_question_latest
    ON attempts (user_id, question_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_attempts_user_answered_at
    ON attempts (user_id, answered_at);
