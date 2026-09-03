ALTER TABLE flashcards ADD COLUMN anki_cid INTEGER;
ALTER TABLE flashcards ADD COLUMN anki_reps INTEGER DEFAULT 0;
ALTER TABLE flashcards ADD COLUMN anki_lapses INTEGER DEFAULT 0;
ALTER TABLE flashcards ADD COLUMN anki_synced_at TEXT;
CREATE INDEX IF NOT EXISTS idx_flashcards_user_anki_cid ON flashcards (user_id, anki_cid);
