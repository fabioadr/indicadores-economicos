# 09 — Plano de Implementação

Sequência de milestones para o Claude Code. Cada milestone é uma sessão idealmente independente.

## Princípios

- Cada milestone produz algo testável de ponta a ponta
- Não pular para o próximo se o atual não estiver verde
- Testes automatizados onde fizer sentido (conectores, agregações)
- Smoke test manual ao final de cada milestone

---

## Milestone 0 — Bootstrap do repositório

**Objetivo:** estrutura de pastas, dependências, scripts básicos.

**Entregas:**

- [✅] `pipeline/` com `requirements.txt` (httpx, python-telegram-bot, matplotlib, pandas, python-dateutil, python-dotenv)
- [✅] `pipeline/.env.example` com todas as variáveis
- [✅] `site/` com `package.json` e Astro inicializado (`pnpm create astro@latest`)
- [✅] `site/` com Tailwind configurado (`pnpm install @astrojs/tailwind tailwindcss`)
- [✅] `data/` (vazio, com `.gitkeep`)
- [✅] `.gitignore` correto (ignorar `.env`, `__pycache__`, `node_modules`, `dist`, `site/dist`, `pipeline/logs/`)
- [✅] `pipeline/cli.py` com argparse esqueleto e comandos no-op
- [✅] `Makefile` ou `scripts/` com atalhos: `make install`, `make collect`, `make build`

**Smoke test:** `python -m pipeline.cli status` roda sem erro (mesmo que vazio).

---

## Milestone 1 — Banco de dados e migrations

**Objetivo:** SQLite funcional, schema aplicado, seeds carregadas.

**Entregas:**

- [✅] `pipeline/db/connection.py` — wrapper sqlite3 com helper para fetch_one, fetch_all, execute
- [✅] `pipeline/db/migrations/001_initial_schema.sql` — schema completo do `03-data-model.md`
- [✅] `pipeline/db/migrations/002_seed_phase1_indicators.sql` — IPCA, CDI, TR
- [✅] `pipeline/cli.py migrate` — aplica migrations pendentes
- [✅] Tabela `_migrations` controla estado
- [✅] Reaplicar migrations é idempotente

**Smoke test:**

```bash
python -m pipeline.cli migrate
sqlite3 data/indicadores.db "SELECT code FROM indicators;"
# Deve listar: IPCA, CDI, TR
```

---

## Milestone 2 — BCB connector

**Objetivo:** buscar dados da API do BCB.

**Entregas:**

- [✅] `pipeline/connectors/base.py` com `BaseConnector`, `RawDataPoint`, `register`, `get_connector`
- [✅] `pipeline/connectors/bcb.py` com `BCBSGSConnector` registrado como `bcb_sgs`
- [✅] Paginação por janelas de 10 anos
- [✅] Tratamento de erros com `FetchError` e `ParseError`
- [✅] Testes em `pipeline/connectors/tests/test_bcb.py` com `respx` mockando httpx
- [✅] Pelo menos 4 casos de teste: janela única, paginação, erro HTTP, JSON malformado

**Smoke test:**

```bash
python -c "
from datetime import date
from pipeline.connectors.bcb import BCBSGSConnector
points = BCBSGSConnector().fetch({'series_id': 433}, since=date(2024, 1, 1))
print(f'{len(points)} pontos coletados')
print(f'Primeiro: {points[0]}')
print(f'Último: {points[-1]}')
"
```

---

## Milestone 3 — Persistência e agregações

**Objetivo:** persistir valores no SQLite e calcular YTD, 12m, 24m, since_inception.

**Entregas:**

- [✅] `pipeline/db/connection.py` — métodos `upsert_value`, `list_values`, `get_last_value_date`, `batch_update_aggregations`
- [✅] `pipeline/core/aggregations.py` com `recompute_aggregations(indicator_id)` e `accumulate(percentages)`
- [✅] Testes unitários em `pipeline/core/tests/test_aggregations.py`:
  - YTD funciona corretamente
  - last_12m retorna NULL com menos de 12 valores
  - since_inception está correto

**Smoke test:**

```bash
python -m pipeline.cli backfill IPCA  # depende do scheduler que vem no próximo
# Após M4, validar:
sqlite3 data/indicadores.db "
SELECT reference_date, value, ytd, last_12m
FROM indicator_values WHERE indicator_id = (SELECT id FROM indicators WHERE code='IPCA')
ORDER BY reference_date DESC LIMIT 5;
"
```

---

## Milestone 4 — Scheduler e CLI de coleta

**Objetivo:** `collect --all`, `collect <code>`, `backfill <code>` funcionando ponta a ponta.

**Entregas:**

- [✅] `pipeline/core/scheduler.py` com `should_collect`, `run_all`, `collect_single`
- [✅] `pipeline/db/connection.py` — métodos para `collection_logs`
- [✅] `pipeline/cli.py` — comandos `collect`, `backfill` plugados
- [✅] Logging configurado em `pipeline/config.py`

**Smoke test:**

```bash
python -m pipeline.cli backfill IPCA
python -m pipeline.cli backfill CDI
python -m pipeline.cli backfill TR

# Validar contagem:
sqlite3 data/indicadores.db "SELECT i.code, COUNT(v.id) FROM indicators i LEFT JOIN indicator_values v ON v.indicator_id = i.id GROUP BY i.code;"
# Esperado: IPCA ~540, CDI ~480, TR ~420
```

---

## Milestone 5 — Builder (JSON + PNG)

**Objetivo:** gerar todos os arquivos derivados que o site vai consumir.

**Entregas:**

- [ ] `pipeline/core/builder.py` — `build()` gera JSONs em `site/data/`
- [ ] `pipeline/core/charts.py` — `generate_chart_current_year`, `generate_chart_history`
- [ ] PNGs em `site/public/charts/`
- [ ] `pipeline/cli.py` — comando `build` plugado
- [ ] Estrutura dos JSONs exatamente como em `05-pipeline.md`

**Smoke test:**

```bash
python -m pipeline.cli build
ls site/data/                # deve ter indicators.json, ipca.json, cdi.json, tr.json
ls site/public/charts/       # deve ter PNGs
cat site/data/indicators.json | jq '.indicators[].code'  # IPCA, CDI, TR
```

---

## Milestone 6 — Site Astro com IPCA hardcoded

**Objetivo:** site renderizando localmente, lendo dos JSONs.

**Entregas:**

- [ ] Layout base (`BaseLayout.astro`, `Header`, `Footer`)
- [ ] Tipografia (Fraunces + Inter via @fontsource)
- [ ] Tailwind com paleta do `06-site.md`
- [ ] Página home `/` listando indicadores da `indicators.json`
- [ ] Página `[slug].astro` lendo `site/data/{slug}.json` e renderizando hero, gráficos, tabela
- [ ] Página `[category]/index.astro` com cards
- [ ] Páginas estáticas: `/sobre/`, `/politica-de-privacidade/`, `/contato/`
- [ ] Disclaimer presente em todas as páginas

**Smoke test:**

```bash
cd site && pnpm dev
# Abrir http://localhost:4321 e validar:
# - Home tem os 3 indicadores
# - /ipca/ /cdi/ /tr/ funcionam e mostram dados
# - /inflacao/ /juros/ /correcao-monetaria/ funcionam
# - Mobile responsivo
```

---

## Milestone 7 — SEO e otimizações

**Objetivo:** Lighthouse > 95 em performance, accessibility e SEO.

**Entregas:**

- [ ] Meta tags por página (title, description, OG)
- [ ] Schema.org JSON-LD em cada página de indicador
- [ ] `sitemap.xml` via `@astrojs/sitemap`
- [ ] `robots.txt`
- [ ] Lazy loading de imagens
- [ ] Preload de fontes
- [ ] Width/height nos PNGs (zero CLS)

**Smoke test:**

```bash
cd site && pnpm build && pnpm preview
# Rodar Lighthouse mobile na home e em /ipca/
# Performance, Accessibility, Best Practices, SEO ≥ 95 cada
```

---

## Milestone 8 — Telegram bot

**Objetivo:** comandos básicos e notificações funcionando.

**Entregas:**

- [ ] `pipeline/bot/handlers.py` — comandos do `07-telegram-bot.md`
- [ ] `pipeline/bot/notifications.py` — funções `send_*`
- [ ] `pipeline/bot/auth.py` — decorator `@authorized_only`
- [ ] `pipeline/bot/__main__.py` — entry point para `python -m pipeline.bot`
- [ ] Pipeline chama `bot.notifications.send_*` em pontos relevantes
- [ ] `scripts/install_systemd.sh` — instala o user service

**Smoke test:**

```bash
python -m pipeline.bot &  # roda em background
# No Telegram:
# /start → resposta de boas-vindas
# /status → resumo
# /coletar IPCA → notificação de coleta
# /publicar → roda build + deploy → notificação
```

---

## Milestone 9 — Deploy e cron

**Objetivo:** sistema rodando 100% automático.

**Entregas:**

- [ ] `pipeline/core/builder.py` — função `deploy()` com git add/commit/push
- [ ] `pipeline/cli.py` — comandos `deploy` e `publish`
- [ ] Repo conectado à Vercel (manual via UI da Vercel)
- [ ] `vercel.json` na raiz com config do `06-site.md`
- [ ] Domínio `indicadoreseconomicoshoje.com.br` apontado para Vercel
- [ ] `scripts/install_cron.sh` — instala entrada no crontab do usuário:
  ```
  0 7 * * * cd ~/indicadoreseconomicos && .venv/bin/python -m pipeline.cli collect --all && .venv/bin/python -m pipeline.cli publish
  ```
- [ ] systemd service do bot ativo
- [ ] `loginctl enable-linger` configurado

**Smoke test:**

```bash
# Deploy manual:
python -m pipeline.cli publish

# Validar:
# - Vercel mostra build em andamento
# - Após 1-2 min, https://indicadoreseconomicoshoje.com.br/ipca/ está no ar
# - Notificação no Telegram

# Validar cron:
crontab -l                  # deve listar a entrada
# Esperar próximo 07:00 ou rodar manualmente:
~/indicadoreseconomicos/.venv/bin/python -m pipeline.cli collect --all
```

---

## Definition of Done global

Para considerar o projeto Fase 1 concluído:

- [ ] Site no ar em `https://indicadoreseconomicoshoje.com.br/`
- [ ] IPCA, CDI e TR com séries históricas completas
- [ ] Cron rodando diariamente sem intervenção manual
- [ ] Bot respondendo aos comandos
- [ ] Lighthouse mobile ≥ 95 em todas as 4 categorias
- [ ] Notificação de erro chega no Telegram quando algo falha
- [ ] README com instruções de setup do zero em outra máquina

---

## Backlog Fase 2 (referência apenas)

Não implementar agora, mas registrar:

- IBGE SIDRA connector
- FGV connector
- Indicadores: SELIC, IGP-M, IGP-DI, INPC, INCC-M
- Filtros de período na tabela histórica (12m, 24m, 5a, total)
- Comparação entre indicadores no mesmo gráfico
- Telegram: agendamento configurável de coleta

## Backlog Fase 3 (referência apenas)

- Calculadora de rentabilidade (R$ X corrigido por Y entre datas)
- Gráficos interativos (Chart.js no cliente)
- Admin web local (visual)
- Sparklines inline na home
