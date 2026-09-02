-- Cartões importados do Anki não possuem uma questão do MedQuest associada.
-- SQLite/libSQL não permite remover uma restrição NOT NULL com ALTER COLUMN;
-- portanto, reconstruímos a tabela preservando todos os dados existentes.
DROP INDEX IF EXISTS idx_flashcards_user_review;
DROP INDEX IF EXISTS idx_flashcards_user_deck;
DROP INDEX IF EXISTS idx_flashcards_user_anki_nid;

ALTER TABLE flashcards RENAME TO flashcards_before_009;

CREATE TABLE flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    front TEXT NOT NULL,
    back TEXT,
    created_at TEXT NOT NULL,
    next_review_date TEXT,
    fsrs_card TEXT,
    user_id TEXT DEFAULT '1',
    source_context TEXT,
    is_ai_generated INTEGER DEFAULT 0,
    report_status TEXT,
    deck_name TEXT DEFAULT 'Geral',
    tags TEXT,
    source_type TEXT DEFAULT 'medquest',
    anki_nid INTEGER
);

INSERT INTO flashcards (
    id, question_id, front, back, created_at, next_review_date, fsrs_card,
    user_id, source_context, is_ai_generated, report_status, deck_name, tags,
    source_type, anki_nid
)
SELECT
    id, question_id, front, back, created_at, next_review_date, fsrs_card,
    user_id, source_context, is_ai_generated, report_status, deck_name, tags,
    source_type, anki_nid
FROM flashcards_before_009;

DROP TABLE flashcards_before_009;

CREATE INDEX IF NOT EXISTS idx_flashcards_user_review
    ON flashcards (user_id, next_review_date);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_deck
    ON flashcards (user_id, deck_name);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_anki_nid
    ON flashcards (user_id, anki_nid);
