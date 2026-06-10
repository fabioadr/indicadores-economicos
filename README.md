# Indicadores Econômicos Hoje

Site estático que publica diariamente indicadores econômicos brasileiros
(inflação, juros, correção monetária, construção civil) com séries históricas,
charts e comparações entre indicadores.

- **Site**: Astro 4 + Tailwind, deploy estático via Vercel
- **Pipeline**: Python 3.12 com SQLite local como fonte da verdade
- **Bot Telegram**: notificações de erro e controle de coleta sob demanda

Stack consciente: sem ORM, sem Docker, free tier de infra. Static-first,
idempotente, fail loud.

## Indicadores publicados

10 indicadores ao vivo, agrupados em 4 categorias:

- **Inflação**: IPCA, IGP-M, IGP-DI, INPC, IPCA-15
- **Juros**: SELIC (anualizada e acumulada), CDI
- **Correção monetária**: TR
- **Construção civil**: INCC-M

Fontes: BCB SGS (maioria) e IBGE SIDRA (IPCA-15).

## Features (estado atual — pós-Fase 2)

- Página de detalhe por indicador com chart, métricas, tabela histórica,
  data da última atualização e data prevista da próxima divulgação
- Filtros de período (12m, 24m, 5a, total) com persistência por slug
- Página `/comparar/` com grupos curados (4 grupos), charts comparativos
- Página `/calendario/` com as próximas datas de divulgação de todos os
  indicadores (datas oficiais do IBGE + estimativas para as demais fontes)
- Bot Telegram com agendamento configurável: `/agendamento`, `/agendar`,
  `/pausar`, `/retomar`, além de `/status`, `/coletar`, `/grupos`, `/migrar`
- Coleta horária via cron com gatekeeping por `schedule_overrides` no DB
- Migrations aplicadas automaticamente no startup do bot e no `/coletar all`,
  para que indicadores recém-adicionados entrem na coleta sem reiniciar nada

## Setup rápido

```bash
git clone <repo>
cd indicadores-economicos
bash scripts/setup.sh                       # cria .venv e instala deps
cp pipeline/.env.example pipeline/.env      # preencher tokens
.venv/bin/python -m pipeline.cli migrate    # aplica schema + seeds
```

Backfill inicial dos indicadores (uma vez):

```bash
for code in IPCA CDI TR SELIC IGPM IGPDI INPC INCCM IPCA15; do
  .venv/bin/python -m pipeline.cli backfill $code
  sleep 5
done
.venv/bin/python -m pipeline.cli build
```

Operação contínua no notebook host:

```bash
bash scripts/install_cron.sh         # cron horário com scheduled-collect
bash scripts/install_systemd.sh      # bot como user service
```

## Comandos principais do CLI

```bash
python -m pipeline.cli status               # diagnóstico geral
python -m pipeline.cli migrate              # aplica migrations pendentes
python -m pipeline.cli collect <CODE>       # coleta um indicador
python -m pipeline.cli collect --all        # coleta todos
python -m pipeline.cli backfill <CODE>      # série histórica completa
python -m pipeline.cli calendar-refresh     # atualiza datas oficiais (IBGE)
python -m pipeline.cli build                # gera site/data + charts
python -m pipeline.cli publish              # build + commit + push
python -m pipeline.cli scheduled-collect    # usado pelo cron horário
```

## Documentação

Specs detalhadas em [docs/](docs/):

- [docs/fase-01/](docs/fase-01/) — visão, arquitetura, modelo de dados,
  conectores, pipeline, site, bot, catálogo, plano de implementação
- [docs/fase-02/](docs/fase-02/) — deltas: SIDRA, comparações, filtros,
  agendamento
- [docs/fase-03/](docs/fase-03/) — calculadora, charts interativos, sparklines
- [docs/fase-04/](docs/fase-04/) — calendário de divulgação e auto-migração
- [docs/fase-05/](docs/fase-05/) — catálogo "em breve" + medição de demanda
- [docs/ROADMAP.md](docs/ROADMAP.md) — próximos passos de evolução da aplicação

[CLAUDE.md](CLAUDE.md) contém o contexto persistente para sessões com
Claude Code.

## Layout do repo

```
pipeline/      # Python: connectors, db, core (collect/build/deploy), bot, cli
site/          # Astro: pages, components, data/, public/charts/
data/          # SQLite (indicadores.db) — não versionado
scripts/       # setup, install_cron, install_systemd, validate-build
tests/         # fixtures + pytest
docs/          # specs por fase
```
