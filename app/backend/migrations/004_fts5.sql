-- Criação da tabela FTS5
CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
    stem,
    explanation
);

-- Popula a tabela com os dados existentes
INSERT INTO questions_fts (rowid, stem, explanation)
SELECT q.id, q.stem, e.explanation_text
FROM questions q
LEFT JOIN explanations e ON q.id = e.question_id;

-- Triggers para questions
CREATE TRIGGER IF NOT EXISTS trg_questions_fts_ins AFTER INSERT ON questions
BEGIN
    INSERT INTO questions_fts(rowid, stem) VALUES (new.id, new.stem);
END;

CREATE TRIGGER IF NOT EXISTS trg_questions_fts_upd AFTER UPDATE OF stem ON questions
BEGIN
    UPDATE questions_fts SET stem = new.stem WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_questions_fts_del AFTER DELETE ON questions
BEGIN
    DELETE FROM questions_fts WHERE rowid = old.id;
END;

-- Triggers para explanations
CREATE TRIGGER IF NOT EXISTS trg_explanations_fts_ins AFTER INSERT ON explanations
BEGIN
    UPDATE questions_fts SET explanation = new.explanation_text WHERE rowid = new.question_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_explanations_fts_upd AFTER UPDATE OF explanation_text ON explanations
BEGIN
    UPDATE questions_fts SET explanation = new.explanation_text WHERE rowid = new.question_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_explanations_fts_del AFTER DELETE ON explanations
BEGIN
    UPDATE questions_fts SET explanation = NULL WHERE rowid = old.question_id;
END;
