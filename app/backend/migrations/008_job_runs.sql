CREATE TABLE IF NOT EXISTS job_runs (
    id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'dry_run')),
    input_hash TEXT NOT NULL,
    output_hash TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_ms INTEGER,
    actor TEXT NOT NULL,
    summary_json TEXT NOT NULL DEFAULT '{}',
    error_class TEXT
);

CREATE INDEX IF NOT EXISTS idx_job_runs_pipeline_started
    ON job_runs (pipeline_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_runs_status_started
    ON job_runs (status, started_at DESC);
