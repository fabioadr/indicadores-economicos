# 02 — Arquitetura

## Diagrama de alto nível

```
┌─────────────────────────────────────────────────────────────┐
│  NOTEBOOK UBUNTU LOCAL (always-on)                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │     cron     │  │ Telegram Bot │  │   Pipeline CLI   │   │
│  │ (07:00 daily)│  │  (long poll) │  │ (manual ops)     │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│         ▼                 ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Pipeline (Python 3.12)                  │    │
│  │                                                       │    │
│  │   ┌────────────┐  ┌─────────────┐  ┌────────────┐   │    │
│  │   │ Connectors │→ │ Aggregations│→ │   Build    │   │    │
│  │   │  (BCB...)  │  │  (YTD, 12m) │  │ (JSON+PNG) │   │    │
│  │   └─────┬──────┘  └──────┬──────┘  └─────┬──────┘   │    │
│  │         │                │                │           │    │
│  │         ▼                ▼                ▼           │    │
│  │   ┌─────────────────────────────────────────────┐   │    │
│  │   │           SQLite (indicadores.db)            │   │    │
│  │   └─────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                                │
│                              ▼                                │
│                     ┌──────────────────┐                      │
│                     │  Local git repo  │                      │
│                     │  /site/data/*    │                      │
│                     │  /site/charts/*  │                      │
│                     └────────┬─────────┘                      │
└──────────────────────────────┼────────────────────────────────┘
                               │ git push origin main
                               ▼
                     ┌──────────────────┐
                     │   GitHub (remote)│
                     └────────┬─────────┘
                              │ webhook
                              ▼
                     ┌──────────────────┐
                     │  Vercel (build)  │
                     │  → CDN global    │
                     └────────┬─────────┘
                              │
                              ▼
              indicadoreseconomicoshoje.com.br
```

## Princípios de design

1. **Static-first** — site público é 100% HTML/CSS, zero runtime, zero banco de dados em produção
2. **Single source of truth** — SQLite local é a fonte; JSONs gerados são derivações versionadas
3. **Pipeline idempotente** — qualquer etapa pode ser re-executada sem efeito colateral
4. **Fail loud** — qualquer erro vira notificação Telegram imediata
5. **Zero infra paga na Fase 1** — Vercel free + GitHub free + notebook próprio
6. **Versionamento como auditoria** — JSON+PNG no git permite rastrear qual dado gerou qual versão
7. **Plugin pattern para fontes** — adicionar nova fonte (FGV, IBGE, etc.) não toca no core

## Stack

| Camada | Tecnologia | Versão |
|---|---|---|
| Runtime do pipeline | Python | 3.12+ |
| Banco de dados local | SQLite | nativo do Python |
| HTTP client | httpx | latest |
| Manipulação de dados | pandas | latest |
| Charts estáticos | matplotlib | latest |
| Bot Telegram | python-telegram-bot | latest stable (v21+) |
| ORM/migrations | SQL puro + sqlite3 | — |
| Site framework | Astro | 4+ |
| Estilo do site | Tailwind CSS | 3+ |
| Hosting | Vercel free tier | — |
| Versionamento | Git + GitHub | — |
| Agendamento | cron (Ubuntu) | — |

**Sem Node frameworks pesados, sem ORMs Python (SQLAlchemy é overkill aqui), sem Docker (não precisa para uma máquina dedicada).**

## Estrutura do repositório

```
indicadoreseconomicos/
├── pipeline/                    # Sistema Python
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py              # Interface BaseConnector
│   │   └── bcb.py               # BCB SGS connector
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py        # Wrapper sqlite3
│   │   ├── schema.sql           # Schema versão atual
│   │   └── migrations/
│   │       ├── 001_initial.sql
│   │       └── ...
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scheduler.py         # Decide o que coletar
│   │   ├── aggregations.py      # YTD, 12m, 24m, since-inception
│   │   ├── builder.py           # Gera JSON + PNG + git push
│   │   └── charts.py            # Geração matplotlib
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py          # /status, /coletar, etc.
│   │   └── notifications.py     # send_success, send_error
│   ├── cli.py                   # Entry point: pipeline collect, pipeline build, etc.
│   ├── config.py                # Carrega .env
│   ├── requirements.txt
│   └── .env.example
│
├── site/                        # Astro
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.astro      # Home
│   │   │   ├── [slug].astro     # Detalhe (gera /ipca, /cdi, /tr)
│   │   │   └── [category]/
│   │   │       └── index.astro  # /inflacao, /juros, etc.
│   │   ├── components/
│   │   ├── layouts/
│   │   └── styles/
│   ├── public/
│   │   └── charts/              # PNGs gerados pelo pipeline
│   ├── data/                    # JSONs gerados pelo pipeline
│   │   ├── indicators.json
│   │   ├── ipca.json
│   │   ├── cdi.json
│   │   └── tr.json
│   ├── astro.config.mjs
│   ├── tailwind.config.mjs
│   ├── tsconfig.json
│   └── package.json
│
├── data/
│   └── indicadores.db           # SQLite (versionado como backup)
│
├── docs/                        # Toda a documentação
│   └── ...
│
├── scripts/
│   ├── install_cron.sh          # Instala entrada no crontab do usuário
│   └── start_bot.sh             # Inicia bot como systemd user service
│
├── .gitignore
├── CLAUDE.md                    # Contexto para Claude Code
└── README.md
```

## Fluxos principais

### Fluxo 1: Coleta diária automática

```
07:00 cron → python -m pipeline.cli collect --all
              ↓
            Para cada indicador ativo:
              ↓
            Verifica se está na hora (frequency vs last_collected_at)
              ↓
            Se sim → connector.fetch() → normalize → persist → recompute_aggregations
              ↓
            Se houve atualização → python -m pipeline.cli build
              ↓
            Build: gera JSONs + PNGs → git add → git commit → git push
              ↓
            Vercel detecta push → build Astro → deploy
              ↓
            Bot envia notificação Telegram
```

### Fluxo 2: Coleta manual via Telegram

```
Usuário no Telegram: /coletar IPCA
              ↓
            Bot recebe comando → executa collect IPCA
              ↓
            Mesmo fluxo de coleta + build + deploy
              ↓
            Bot responde com resumo
```

### Fluxo 3: Backfill histórico (apenas primeira execução)

```
python -m pipeline.cli backfill <indicator-code>
              ↓
            Pagina por janelas de 10 anos (limite BCB)
              ↓
            Persiste todo o histórico
              ↓
            Recalcula agregações para a série inteira
```

## Decisões registradas

| Decisão | Escolha | Alternativas | Motivo |
|---|---|---|---|
| Banco | SQLite | DuckDB, Postgres | Volume tiny, zero infra |
| Pipeline lang | Python | Node, Go | Ecossistema de dados |
| Site framework | Astro | Next.js, Hugo | Static-first, zero JS, build rápido |
| Charts | PNG via matplotlib | Chart.js, D3 | Static-first; interativo na Fase 3 |
| Hosting | Vercel free | S3+CloudFront, Netlify | Git push → deploy |
| Agendamento | cron | n8n, GitHub Actions | Zero infra extra |
| Notificação | Telegram | Email, Slack | Mobile, gratuito, interativo |
| Bot framework | python-telegram-bot | aiogram | Estabilidade, comunidade |
| Versionamento de dados | Git | S3 versionado | Auditoria + rollback simples |
| Sem ORM | SQL puro | SQLAlchemy | 4 tabelas, queries simples |
| Sem Docker | Execução nativa | Container | Máquina dedicada, simplificação |

## Operação contínua

- **Pipeline**: cron dispara `pipeline.cli collect --all` todo dia 07:00
- **Bot**: roda como `systemd --user` service, sempre ligado
- **Backup**: SQLite vai para o git no commit do build (snapshot diário implícito)
- **Logs**: arquivo `pipeline/logs/{YYYY-MM-DD}.log` rotacionado por dia
- **Update do código**: `git pull` no notebook + restart do bot service
