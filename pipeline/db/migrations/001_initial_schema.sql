-- 001 — Initial schema
-- Mirrors docs/03-data-model.md. Idempotent via IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS indicators (
    id                   TEXT PRIMARY KEY,
    code                 TEXT UNIQUE NOT NULL,
    slug                 TEXT UNIQUE NOT NULL,
    name                 TEXT NOT NULL,
    short_description    TEXT NOT NULL,
    long_description     TEXT NOT NULL,
    category             TEXT NOT NULL,
    unit                 TEXT NOT NULL DEFAULT 'percent',
    frequency            TEXT NOT NULL,
    source_name          TEXT NOT NULL,
    source_url           TEXT NOT NULL,
    connector_type       TEXT NOT NULL,
    connector_config     TEXT NOT NULL,
    inception_date       TEXT NOT NULL,
    expected_release_day INTEGER,
    active               INTEGER NOT NULL DEFAULT 1,
    meta_title           TEXT NOT NULL,
    meta_description     TEXT NOT NULL,
    last_collected_at    TEXT,
    last_built_at        TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS indicator_values (
    id              TEXT PRIMARY KEY,
    indicator_id    TEXT NOT NULL,
    reference_date  TEXT NOT NULL,
    value           REAL NOT NULL,
    ytd             REAL,
    last_12m        REAL,
    last_24m        REAL,
    since_inception REAL,
    raw_value       TEXT,
    collected_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (indicator_id, reference_date),
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_values_indicator_date
    ON indicator_values(indicator_id, reference_date DESC);

CREATE TABLE IF NOT EXISTS collection_logs (
    id              TEXT PRIMARY KEY,
    indicator_id    TEXT,
    triggered_by    TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    status          TEXT NOT NULL,
    records_added   INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message   TEXT,
    raw_response    TEXT,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_collection_started
    ON collection_logs(started_at DESC);

CREATE TABLE IF NOT EXISTS build_logs (
    id                 TEXT PRIMARY KEY,
    triggered_by       TEXT NOT NULL,
    started_at         TEXT NOT NULL,
    finished_at        TEXT,
    status             TEXT NOT NULL,
    indicators_updated TEXT,
    files_generated    INTEGER,
    git_commit_sha     TEXT,
    error_message      TEXT
);

CREATE INDEX IF NOT EXISTS idx_build_started
    ON build_logs(started_at DESC);
