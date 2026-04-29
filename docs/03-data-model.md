# 03 — Modelo de Dados

## Database: SQLite

Localização: `data/indicadores.db` (relativo ao root do repositório).

Versionado no git como backup. O arquivo cresce devagar (kilobytes por mês), o impacto no tamanho do repositório é desprezível.

## Schema (versão 1)

```sql
-- Definição de cada indicador disponível
CREATE TABLE indicators (
    id                  TEXT PRIMARY KEY,         -- UUID v4
    code                TEXT UNIQUE NOT NULL,     -- 'IPCA', 'CDI', 'TR'
    slug                TEXT UNIQUE NOT NULL,     -- 'ipca', 'cdi', 'tr' (URL)
    name                TEXT NOT NULL,            -- 'IPCA - Índice de Preços ao Consumidor Amplo'
    short_description   TEXT NOT NULL,            -- 1 frase para cards
    long_description    TEXT NOT NULL,            -- markdown, para a página
    category            TEXT NOT NULL,            -- 'inflacao' | 'juros' | 'correcao_monetaria'
    unit                TEXT NOT NULL DEFAULT 'percent',  -- 'percent' | 'index'
    frequency           TEXT NOT NULL,            -- 'monthly' | 'biweekly' | 'daily'
    source_name         TEXT NOT NULL,            -- 'Banco Central do Brasil', 'IBGE', 'FGV'
    source_url          TEXT NOT NULL,            -- URL pública institucional para citar
    connector_type      TEXT NOT NULL,            -- 'bcb_sgs' | 'ibge_sidra' | 'custom_http'
    connector_config    TEXT NOT NULL,            -- JSON com parâmetros do conector
    inception_date      TEXT NOT NULL,            -- YYYY-MM-DD, primeira data disponível na fonte
    expected_release_day INTEGER,                 -- dia do mês em que costuma ser divulgado (NULL se variável)
    active              INTEGER NOT NULL DEFAULT 1,
    meta_title          TEXT NOT NULL,            -- SEO title template, ex: '{name} - Tabela atualizada {month}/{year}'
    meta_description    TEXT NOT NULL,            -- SEO description template
    last_collected_at   TEXT,                     -- ISO 8601
    last_built_at       TEXT,                     -- ISO 8601
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Valor por período de cada indicador
CREATE TABLE indicator_values (
    id                  TEXT PRIMARY KEY,         -- UUID v4
    indicator_id        TEXT NOT NULL,
    reference_date      TEXT NOT NULL,            -- YYYY-MM-01 (sempre 1º do mês para mensais)
    value               REAL NOT NULL,            -- valor do período em percentual (ex: 0.44 = 0,44%)
    ytd                 REAL,                     -- acumulado no ano corrente até este período
    last_12m            REAL,                     -- acumulado 12 meses até este período
    last_24m            REAL,                     -- acumulado 24 meses até este período
    since_inception     REAL,                     -- acumulado desde o primeiro valor da série
    raw_value           TEXT,                     -- valor original da fonte (string), para auditoria
    collected_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (indicator_id, reference_date),
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE
);

CREATE INDEX idx_values_indicator_date ON indicator_values(indicator_id, reference_date DESC);

-- Log de cada execução de coleta
CREATE TABLE collection_logs (
    id              TEXT PRIMARY KEY,
    indicator_id    TEXT,                         -- NULL para coletas all
    triggered_by    TEXT NOT NULL,                -- 'cron' | 'telegram' | 'cli' | 'backfill'
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    status          TEXT NOT NULL,                -- 'success' | 'error' | 'skipped' | 'partial'
    records_added   INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message   TEXT,
    raw_response    TEXT,                         -- snippet da resposta para debug
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE SET NULL
);

CREATE INDEX idx_collection_started ON collection_logs(started_at DESC);

-- Log de cada execução de build/deploy
CREATE TABLE build_logs (
    id                  TEXT PRIMARY KEY,
    triggered_by        TEXT NOT NULL,            -- 'cron' | 'telegram' | 'cli'
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    status              TEXT NOT NULL,            -- 'success' | 'error' | 'no_changes'
    indicators_updated  TEXT,                     -- JSON array de codes: ["IPCA","TR"]
    files_generated     INTEGER,
    git_commit_sha      TEXT,
    error_message       TEXT
);

CREATE INDEX idx_build_started ON build_logs(started_at DESC);
```

## Convenções de tipos

- **TEXT** para datas/timestamps: SQLite não tem tipo data nativo; usamos ISO 8601 sempre
- **REAL** para valores percentuais: `0.44` significa 0,44% (não dividir por 100 ao armazenar; armazenar como veio da fonte)
- **JSON serializado em TEXT** para `connector_config` e `indicators_updated`
- **INTEGER 0/1** para boolean (`active`)

## connector_config — exemplos por tipo

### bcb_sgs

```json
{
  "series_id": 433,
  "value_format": "percent_monthly"
}
```

- `series_id`: código numérico da série no SGS
- `value_format`: para indicar interpretação ("percent_monthly", "percent_annual", "index", "factor")

### Para outros conectores (futuro)

A estrutura é livre — cada connector documenta seu próprio schema de config.

## Migrations

- Cada migration é um arquivo `.sql` em `pipeline/db/migrations/`
- Nomenclatura: `NNN_descricao.sql` (zero-padded a 3 dígitos)
- Estado controlado por uma tabela `_migrations`:

```sql
CREATE TABLE IF NOT EXISTS _migrations (
    name        TEXT PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- O comando `pipeline.cli migrate` aplica pending migrations em ordem
- Migrations só vão para frente — sem rollback automático

## Seeds (catálogo inicial de indicadores)

Os indicadores da Fase 1 são inseridos via migration `002_seed_phase1_indicators.sql`. O conteúdo dessa seed está em `08-indicators-catalog.md`.

## Cálculo das agregações (referência)

Todos os indicadores da Fase 1 são percentuais mensais que compõem geometricamente.

### Acumulado N meses

```python
def accumulate(values: list[float]) -> float:
    """values: lista de valores percentuais, ex: [0.44, 0.31, 0.61]
    retorna: percentual acumulado, ex: 1.37"""
    factor = 1.0
    for v in values:
        factor *= (1 + v / 100)
    return (factor - 1) * 100
```

### YTD (acumulado no ano)

Para cada `reference_date`, pega todos os valores do mesmo ano com `reference_date <= o atual` e aplica `accumulate()`.

### last_12m / last_24m

Para cada `reference_date`, pega os 12 (ou 24) valores anteriores **inclusive o atual** ordenados por data, e aplica `accumulate()`. Se houver menos de 12/24 valores disponíveis na série, o campo fica `NULL` para esse período.

### since_inception

Para cada `reference_date`, aplica `accumulate()` sobre todos os valores desde o primeiro da série até o atual.

### Quando recalcular

- Ao inserir um novo valor para um indicador → recalcular **todos os valores** desse indicador (impacto cascata em rolling windows)
- Em prática, com poucas centenas de linhas por indicador, isso roda em milissegundos
