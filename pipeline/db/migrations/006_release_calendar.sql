-- 006 — Calendário de divulgação (datas oficiais de release)
--
-- Motivação:
--   Os connectors (BCB SGS / IBGE SIDRA) não retornam a data prevista da próxima
--   divulgação. Para os indicadores do IBGE (IPCA, INPC, IPCA-15) existe a API
--   oficial de calendário (servicodados.ibge.gov.br/api/v3/calendario). Esta
--   tabela guarda as datas oficiais futuras coletadas dali. Indicadores sem
--   fonte oficial (FGV, BCB) usam estimativa calculada em tempo de build a partir
--   de `expected_release_day` — não são persistidos aqui.

CREATE TABLE IF NOT EXISTS release_dates (
    id               TEXT PRIMARY KEY,
    indicator_id     TEXT NOT NULL,
    release_date     TEXT NOT NULL,            -- YYYY-MM-DD
    reference_period TEXT,                     -- YYYY-MM (período de referência, se conhecido)
    source           TEXT NOT NULL,            -- 'ibge'
    title            TEXT,                     -- título da divulgação na fonte
    fetched_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (indicator_id, release_date),
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_release_dates_indicator_date
    ON release_dates(indicator_id, release_date);
