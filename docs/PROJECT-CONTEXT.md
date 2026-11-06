# Contexto do projeto — estado atual

Complementa o `AGENTS.md` (raiz) com decisões por área, catálogo e status das fases. Leia sob demanda.
Specs históricas por fase ficam em `docs/fase-0N/` e descrevem a intenção **na época**; quando divergirem
deste documento ou do código, vale o código.

Última revisão: 2026-11-05.

## 1. Status das fases

| Fase | Escopo | Status |
|---|---|---|
| 1 (`docs/fase-01/`) | Pipeline BCB SGS, SQLite, build JSON/PNG, site Astro, bot Telegram, cron | Implementada |
| 2 (`docs/fase-02/`) | Conector IBGE SIDRA, novos índices, `/comparar/` (PNG), filtros de período, agendamento via bot | Implementada |
| 3 (`docs/fase-03/`) | Calculadora de correção, Chart.js, sparklines, `calculator_enabled`, IPC-Fipe/PIM-PF | **Só especificada, não implementada** |
| 4 (`docs/fase-04/`) | Auto-migração no bot, calendário de divulgação (`release_dates`, `/calendario/`) | Implementada |
| 5 (`docs/fase-05/`) | Páginas "em breve" para medir demanda (GSC + GA4) | **Só especificada, não implementada** |
| Fora de fase | Indicadores de poupança, mercado imobiliário e salário mínimo (migrations 005, 008, 009); `aggregation_mode`; módulo GSC (010) | Implementado |

Consequências práticas: não existe calculadora, Chart.js, sparklines nem coluna `calculator_enabled`;
os gráficos são PNG (matplotlib) e `/comparar/` usa PNGs pré-renderizados. `scripts/validate-fase3-build.sh`
está vazio. Próximos passos priorizados em `docs/ROADMAP.md`.

## 2. Catálogo de indicadores (16 ativos)

Fonte da verdade: tabela `indicators`. Esta tabela é um retrato de 2026-11-05.

| Code | Slug (URL `/<slug>/`) | Categoria | Conector / config | Unidade | aggregation_mode |
|---|---|---|---|---|---|
| IPCA | ipca | inflacao | bcb_sgs 433 | percent | compound_monthly |
| IPCA15 | ipca-15 | inflacao | ibge_sidra 3065 / 355 / N1[all] | percent | compound_monthly |
| INPC | inpc | inflacao | bcb_sgs 188 | percent | compound_monthly |
| IGPM | igp-m | inflacao | bcb_sgs 189 (espelho FGV) | percent | compound_monthly |
| IGPDI | igp-di | inflacao | bcb_sgs 190 (espelho FGV) | percent | compound_monthly |
| SELIC | selic | juros | bcb_sgs 4189 (anualizada) | percent | none |
| SELICAC | selic-acumulada | juros | bcb_sgs 4390 | percent | compound_monthly |
| CDI | cdi | juros | bcb_sgs 4391 | percent | compound_monthly |
| TR | tr | correcao_monetaria | bcb_sgs 226 (diária) | percent | compound_daily_to_monthly |
| INCCM | incc-m | construcao_civil | bcb_sgs 192 (espelho FGV) | percent | compound_monthly |
| POUPREN | poupanca-rentabilidade | poupanca | bcb_sgs 195 | percent | compound_daily_to_monthly |
| POUPSAL | poupanca-saldo | poupanca | bcb_sgs 7836 | brl_millions | level |
| FINIMOB | financiamento-imobiliario-concessoes | mercado_imobiliario | bcb_sgs 20704 | brl_millions | level |
| FINISAL | financiamento-imobiliario-saldo | mercado_imobiliario | bcb_sgs 20611 | brl_millions | level |
| IVGR | ivg-r | mercado_imobiliario | bcb_sgs 21340 | index | level |
| SALMIN | salario-minimo | trabalho | bcb_sgs 1619 | brl | level |

Categorias válidas: as do tipo `CategoryKey` em `site/src/lib/data.ts`. A URL da categoria troca `_` por `-`
(`/construcao-civil/`, `/mercado-imobiliario/`).

## 3. Decisões por área

### Conectores (`pipeline/connectors/`)
- Plugin pattern: cada conector estende `BaseConnector` e se registra com o decorator `@register("<nome>")`
  (`base.py`); o nome é o `connector_type` do indicador.
- BCB SGS: janelas de busca paginadas; sem `since`, o default do conector é 1986-01-01.
  O backfill usa `indicators.inception_date`.
- IBGE SIDRA: células `-`/`...` são tratadas como ausência de dado (comportamento esperado).
- FGV (IGP-M, IGP-DI, INCC-M) entra pelo espelho no SGS. Conector FGV nativo é exploratório (ROADMAP).
- IPCA continua no SGS (decisão da Fase 2 de não migrar para SIDRA).

### Agregações (`pipeline/core/aggregations.py`)
`indicators.aggregation_mode` controla YTD / 12m / 24m / desde o início:
- `compound_monthly` (padrão): composição geométrica das variações mensais.
- `compound_daily_to_monthly`: séries diárias reduzidas ao último valor do mês antes de compor.
- `none`: série não composta (SELIC anualizada); colunas agregadas ficam `NULL`.
- `level`: nível absoluto (saldo, fluxo, índice); agregadas viram variação % do nível.

Salário mínimo tem derivados próprios (vigências, valor diário/horário) em `pipeline/core/wage.py`.

### Build e site
- `builder.build` gera `site/data/<slug>.json`, `indicators.json`, `groups.json`, `calendar.json` e PNGs em
  `site/public/charts/` (`<slug>-history.png`, `<slug>-<ano>.png`, `compare-<grupo>.png`).
- Páginas por `getStaticPaths` a partir desses JSONs: `/<slug>/`, `/<categoria>/`, `/comparar/<grupo>/`,
  `/calendario/`, além de `sobre`, `contato` e `politica-de-privacidade`.
- JS no cliente: mínimo, sem framework, ~5KB gzipped no total (filtro de período com persistência
  em `localStorage`). Conteúdo principal precisa funcionar sem JS.
- Tracking: GA4, AdSense e Meta Pixel no `BaseLayout.astro`. Mudanças exigem pedido explícito e atenção a
  consentimento e deduplicação.

### Comparações (`/comparar/`)
Grupos curados em `pipeline/config_groups.py` (`INDICATOR_GROUPS`), renderizados em PNG.
Sem comparação livre. Fluxo: skill `add-comparison-group`; regeneração: `bash scripts/regenerate-comparisons.sh`.

### Agendamento
- cron do sistema chama `scheduled-collect` de hora em hora; o comando consulta `schedule_overrides` e coleta
  se o horário agendado mais recente ainda não rodou (`is_due` em `pipeline/core/cron.py`: compara com
  `last_run_at`; `datetime.now()` sem timezone, então vale o fuso do processo, America/Sao_Paulo).
- Recuperação de execução perdida (desde 2026-11-05): o host é um desktop e o WSL só sobe após o logon, então
  a hora agendada muitas vezes passa com a máquina desligada. A coleta roda na primeira hora cheia seguinte;
  vários dias perdidos viram uma única coleta (é idempotente). Antes disso, o gate exigia a hora exata e a
  coleta agendada ficou parada de 30/10 a 05/11/2026.
- Horário muda pelo bot: `/agendamento`, `/agendar <cron>` (no máximo 1x/hora), `/pausar`, `/retomar`.

### Calendário de divulgação (Fase 4)
- `release_dates` guarda só datas **oficiais** (IBGE: IPCA, INPC, IPCA-15), atualizadas na coleta
  (`refresh_official_dates`, fail-soft) ou via `calendar-refresh`.
- Demais indicadores usam estimativa calculada no build a partir de `expected_release_day`.
- O build nunca faz chamada de rede.

### Auto-migração (Fase 4)
O bot roda `apply_pending_migrations` no startup e no `/coletar all`; `/migrar` aplica sob demanda.
`should_collect()` trata `last_collected_at IS NULL` como coletável, então indicador novo entra na próxima coleta.

### Search Console (`pipeline/gsc/`)
Coleta semanal (cron de segunda 08h) para as tabelas `gsc_*` e relatório. Credenciais da conta de serviço em
`pipeline/secrets/gsc-sa.json` (fora do git). Setup em `docs/gsc/SETUP.md`.

## 4. Variáveis de ambiente (`pipeline/.env`, ver `.env.example`)

`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_REPO_PATH`, `DB_PATH`, `SITE_DATA_DIR`, `SITE_CHARTS_DIR`,
`LOG_LEVEL`, `GSC_SITE_URL`, `GSC_CREDENTIALS_PATH`.

## 5. Quando estiver em dúvida

1. Escopo/arquitetura: este documento, depois a spec da fase relevante em `docs/fase-0N/`.
2. Decisão arquitetural não coberta: perguntar antes de implementar.
3. Detalhe de implementação: escolher a opção mais simples e documentar.
