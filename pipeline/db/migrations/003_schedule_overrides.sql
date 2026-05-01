-- 003 — Schedule overrides table + default seed
-- Tabela usada por `pipeline.cli scheduled-collect` (Fase 2) para decidir,
-- a cada execução do cron, se deve disparar a coleta. Apenas uma linha
-- ativa por vez (convenção: única com enabled = 1).

CREATE TABLE IF NOT EXISTS schedule_overrides (
    id              TEXT PRIMARY KEY,
    cron_expression TEXT NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    last_run_at     TEXT,
    next_run_at     TEXT,
    description     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO schedule_overrides (id, cron_expression, enabled, description)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    '0 7 * * *',
    1,
    'Agendamento padrão Fase 1'
);
