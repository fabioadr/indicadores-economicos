# Documentação — Indicadores Econômicos Hoje · Fase 4

Incremento focado, **já implementado**, sobre as Fases 1–3 em produção. Dois
objetivos:

1. **Auto-migração na coleta** — `/coletar all` passou a enxergar indicadores
   recém-adicionados sem intervenção manual.
2. **Calendário de divulgação** — cada indicador mostra a data da última
   atualização e a data prevista da próxima divulgação; nova página `/calendario/`.

## Princípios herdados (não revisados)

Static-first; SQLite local é a single source of truth; plugin pattern;
idempotência; fail loud (Telegram); versionamento de dados via git. **Rede roda
na coleta; o build é puro a partir do DB.**

## 1. Auto-migração na coleta

**Problema:** o bot Telegram (`pipeline/bot/__main__.py`) nunca aplicava
migrations pendentes — só o CLI `migrate` fazia. Como indicadores novos entram
via migration SQL (skill `add-indicator`), no ambiente do bot o indicador só
aparecia depois de alguém rodar `pipeline.cli migrate` naquele DB. A lógica de
`should_collect()` já cobria indicador novo (`last_collected_at IS NULL` →
`True`); o gargalo era a migration não aplicada.

**Correção:**

- `main()` do bot aplica `apply_pending_migrations` no **startup**.
- `/coletar all` aplica migrations **antes** de `run_all` (não precisa
  reiniciar o bot) e avisa quais foram aplicadas.
- Novo comando **`/migrar`** para aplicar migrations sob demanda, com retorno
  no chat. Listado no `/help`.

## 2. Calendário de divulgação (híbrido)

Os connectors (BCB SGS / IBGE SIDRA) não retornam data de próxima divulgação.
Estratégia híbrida:

- **Oficial (IBGE):** API de calendário
  `https://servicodados.ibge.gov.br/api/v3/calendario?de=&ate=` cobre IPCA,
  INPC e IPCA-15. As datas futuras são buscadas na coleta e persistidas na
  tabela `release_dates`.
- **Estimada (demais):** calculada em tempo de build a partir de
  `indicators.expected_release_day` + frequência. Para mensais: a referência
  seguinte é divulgada ~2 meses após a última referência, no dia esperado,
  rolando para frente se a data já passou. Marcada como `estimated` na UI
  (sufixo "(estimativa)").

### Cobertura

| Fonte                        | Indicadores                                  |
| ---------------------------- | -------------------------------------------- |
| Oficial (IBGE calendar API)  | IPCA, INPC, IPCA-15                           |
| Estimada (expected_release_day) | IGP-M, IGP-DI, INCC-M, SELIC, SELICAC, CDI, TR |

### Schema — tabela nova `release_dates`

Migration `pipeline/db/migrations/006_release_calendar.sql`:

| Coluna             | Tipo | Notas                                  |
| ------------------ | ---- | -------------------------------------- |
| `id`               | TEXT | UUID v4 (PK)                            |
| `indicator_id`     | TEXT | FK → indicators(id) ON DELETE CASCADE  |
| `release_date`     | TEXT | YYYY-MM-DD                             |
| `reference_period` | TEXT | YYYY-MM (período de referência, se houver) |
| `source`           | TEXT | `'ibge'`                               |
| `title`            | TEXT | título da divulgação na fonte          |
| `fetched_at`       | TEXT | ISO; atualizado no upsert               |

`UNIQUE(indicator_id, release_date)` + índice `(indicator_id, release_date)`.
Indicadores sem fonte oficial **não** são persistidos aqui (a estimativa é
calculada no build). `get_next_official_release_dates(conn, today)` retorna a
menor `release_date` futura por indicador (`MIN`), robusta a duplicatas.

### Pipeline

- **`pipeline/core/release_calendar.py`** (novo): `fetch_ibge_calendar`,
  `refresh_official_dates` (fail-soft), `estimated_next_release`,
  `next_release_for` (oficial > estimada).
- **`run_all`** chama `refresh_official_dates` no início (fail-soft, nunca
  derruba a coleta).
- **CLI `calendar-refresh`** atualiza as datas oficiais manualmente.
- **`builder.py`**: os JSONs de índice e detalhe ganharam `last_collected_at` e
  `next_release` (`{date, source}`); novo `site/data/calendar.json` ordenado
  pela próxima divulgação. Segue o padrão de `groups.json`: escrito sempre no
  caminho de sucesso; no caminho `no_changes`, só se faltar.

### Site

- `site/src/lib/data.ts`: tipos `NextRelease`, `CalendarEntry`, `CalendarIndex`
  + `loadCalendar()`; campos novos em `IndicatorSummary`/`IndicatorDetail`.
- `IndicatorHero.astro`: "Atualizado em" + "Próxima divulgação" (sufixo
  "(estimativa)" quando aplicável).
- `IndicatorCard.astro`: linha "Próxima: dd/mm" (home + páginas de categoria).
- **Nova página `/calendario/`** (tabela ordenada por data) + link na navegação
  (`Header.astro`).

## Arquivos-chave

```
pipeline/bot/__main__.py                       # migrations no startup + /migrar
pipeline/bot/handlers.py                       # cmd_migrar, migrate no /coletar all
pipeline/bot/formatters.py                     # /migrar no help
pipeline/db/migrations/006_release_calendar.sql
pipeline/core/release_calendar.py              # IBGE + estimativa + next_release
pipeline/db/connection.py                      # upsert_release_date, get_next_official_release_dates
pipeline/core/scheduler.py                     # refresh no run_all (fail-soft)
pipeline/core/builder.py                       # next_release/last_collected_at + calendar.json
pipeline/cli.py                                # comando calendar-refresh
site/src/lib/data.ts                           # tipos + loadCalendar
site/src/components/domain/IndicatorHero.astro
site/src/components/domain/IndicatorCard.astro
site/src/pages/calendario/index.astro
site/src/components/layout/Header.astro        # link Calendário
```

## Fora de escopo

- Datas oficiais para FGV (IGP-M/DI, INCC-M) e BCB (SELIC/CDI/TR): ficam na
  estimativa. Curadoria futura pode reusar `release_dates` com outro `source`.
