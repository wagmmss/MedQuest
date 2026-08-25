-- Audit trail for AI-assisted taxonomy review. These tables never replace the
-- published questions.area/questions.subtema values directly.
CREATE TABLE IF NOT EXISTS classification_runs (
    id TEXT PRIMARY KEY,
    taxonomy_version TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('created', 'reviewing', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS classification_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES classification_runs(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    reviewer_role TEXT NOT NULL CHECK (reviewer_role IN ('triage', 'classifier', 'critic', 'adjudicator')),
    decision TEXT NOT NULL CHECK (decision IN ('classify', 'abstain')),
    proposed_area TEXT,
    proposed_subtema TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence TEXT NOT NULL,
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (status IN ('proposed', 'accepted', 'rejected', 'needs_human_review')),
    created_at TEXT NOT NULL,
    UNIQUE(run_id, question_id, reviewer_role)
);

CREATE TABLE IF NOT EXISTS classification_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL REFERENCES classification_proposals(id),
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('accept', 'reject', 'override', 'ambiguous')),
    final_area TEXT,
    final_subtema TEXT,
    rationale TEXT NOT NULL,
    reviewed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_classification_proposals_run_status
    ON classification_proposals(run_id, status);
CREATE INDEX IF NOT EXISTS idx_classification_proposals_question
    ON classification_proposals(question_id);
CREATE INDEX IF NOT EXISTS idx_classification_reviews_proposal
    ON classification_reviews(proposal_id);
