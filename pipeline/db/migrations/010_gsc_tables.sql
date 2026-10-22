-- 010 — Google Search Console (performance diário)
--
-- Grain diário para tendência e antes/depois de mudanças de título.
-- Coleta via Search Console API; análise semanal é derivada (não persistida).
-- Idempotente: PK natural + ON CONFLICT no upsert da aplicação.

CREATE TABLE IF NOT EXISTS gsc_sync_log (
    id             TEXT PRIMARY KEY,
    triggered_by   TEXT NOT NULL,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT NOT NULL,
    data_state     TEXT NOT NULL,
    start_date     TEXT,
    end_date       TEXT,
    days_ok        INTEGER DEFAULT 0,
    rows_upserted  INTEGER DEFAULT 0,
    error_message  TEXT
);

CREATE INDEX IF NOT EXISTS idx_gsc_sync_started
    ON gsc_sync_log(started_at DESC);

CREATE TABLE IF NOT EXISTS gsc_query_daily (
    date         TEXT NOT NULL,
    query        TEXT NOT NULL,
    clicks       REAL NOT NULL,
    impressions  REAL NOT NULL,
    ctr          REAL NOT NULL,
    position     REAL NOT NULL,
    PRIMARY KEY (date, query)
);

CREATE INDEX IF NOT EXISTS idx_gsc_query_date
    ON gsc_query_daily(date);

CREATE TABLE IF NOT EXISTS gsc_page_daily (
    date            TEXT NOT NULL,
    page            TEXT NOT NULL,
    canonical_path  TEXT NOT NULL,
    clicks          REAL NOT NULL,
    impressions     REAL NOT NULL,
    ctr             REAL NOT NULL,
    position        REAL NOT NULL,
    PRIMARY KEY (date, page)
);

CREATE INDEX IF NOT EXISTS idx_gsc_page_date
    ON gsc_page_daily(date);

CREATE INDEX IF NOT EXISTS idx_gsc_page_canonical
    ON gsc_page_daily(canonical_path);

CREATE TABLE IF NOT EXISTS gsc_query_page_daily (
    date            TEXT NOT NULL,
    query           TEXT NOT NULL,
    page            TEXT NOT NULL,
    canonical_path  TEXT NOT NULL,
    clicks          REAL NOT NULL,
    impressions     REAL NOT NULL,
    ctr             REAL NOT NULL,
    position        REAL NOT NULL,
    PRIMARY KEY (date, query, page)
);

CREATE INDEX IF NOT EXISTS idx_gsc_query_page_date
    ON gsc_query_page_daily(date);

CREATE TABLE IF NOT EXISTS gsc_appearance_daily (
    date                TEXT NOT NULL,
    search_appearance   TEXT NOT NULL,
    clicks              REAL NOT NULL,
    impressions         REAL NOT NULL,
    ctr                 REAL NOT NULL,
    position            REAL NOT NULL,
    PRIMARY KEY (date, search_appearance)
);

CREATE INDEX IF NOT EXISTS idx_gsc_appearance_date
    ON gsc_appearance_daily(date);
