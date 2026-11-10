# AGENTS.md

Instruções para qualquer agente de código (Claude Code, Codex, Cursor, Copilot, Gemini etc.) e para
pessoas. Este arquivo é a fonte única; arquivos específicos de ferramenta (`CLAUDE.md`, `.claude/`)
só acrescentam o que é exclusivo daquela ferramenta.

## 1. Regras de ambiente (leia antes de executar qualquer coisa)

- **Python é sempre `.venv/bin/python`** (CPython 3.14 gerenciado pelo uv, isolado do Python do sistema).
  A versão menor está em `.python-version`; o patch acompanha `uv python upgrade 3.14`.
  Ferramentas: `.venv/bin/pytest`, `.venv/bin/ruff`. Não procure outros interpretadores, não use
  `python`/`python3`/`pip` soltos e não escreva scripts para descobrir o ambiente: ele já está definido aqui.
- Dependências ficam no `pyproject.toml` (runtime em `project.dependencies`, ferramentas em
  `[dependency-groups] dev`) e as versões exatas no `uv.lock`. Acrescentar pacote: `uv add <pacote>`
  ou `uv add --dev <pacote>`. Recriar o ambiente: `uv sync` (o `bash scripts/setup.sh` faz isso e
  também o `pnpm install` do site). O projeto não é um pacote publicável: o uv só instala as
  dependências. Cron, bot e agentes chamam `.venv/bin/python`; `uv run` é equivalente no terminal.
- Site: Node 24 + **pnpm** (nunca npm/yarn), sempre dentro de `site/`.
- O repositório fica num disco separado montado pelo Windows em `/mnt/wsl/dev` (`~/repos` é symlink).
  Antes de escrever arquivos, confirme `mountpoint -q /mnt/wsl/dev`. Sem o disco, nada funciona.
- Segredos: `pipeline/.env` e `pipeline/secrets/` (chave da conta de serviço do GSC). Nunca leia,
  imprima, copie para logs ou commite. Use `pipeline/.env.example` como referência de variáveis.
- `pipeline/logs/` pode ser grande: consulte primeiro as tabelas de log do banco (seção 6).

## 2. O projeto

**Indicadores Econômicos Hoje** (https://indicadoreseconomicoshoje.com.br) é um site estático que
publica indicadores econômicos brasileiros com séries históricas, gráficos, comparações e calendário
de divulgação. Um pipeline Python local coleta dados do BCB e do IBGE, grava num SQLite e gera os
artefatos que o site consome. O deploy é um `git push` (Vercel).

Princípios (não desviar sem combinar):

- **Static-first**: site 100% estático, sem runtime nem banco em produção.
- **SQLite local é a fonte da verdade** (`data/indicadores.db`, versionado no git); JSONs e PNGs são derivados.
- **Idempotência**: qualquer comando pode ser re-executado sem efeito colateral.
- **Fail loud**: erro vira notificação no Telegram, nunca falha silenciosa.
- **Plugin pattern**: conector novo não toca o core (`pipeline/connectors/`).
- **Simplicidade e free tier**: sem ORM, sem Docker, sem backend, sem framework JS no cliente.

## 3. Stack

| Camada | Tecnologia |
|---|---|
| Pipeline | Python 3.14 (uv), `sqlite3` puro, httpx, pandas, matplotlib, croniter, python-telegram-bot ≥21 (async), google-auth (GSC) |
| Testes/lint | pytest + respx (mocks HTTP), ruff |
| Site | Astro 7 + Tailwind 4 (`@tailwindcss/vite`, sem `tailwind.config`), TypeScript strict, `@astrojs/sitemap` |
| Fontes de dados | BCB SGS (`bcb_sgs`) e IBGE SIDRA (`ibge_sidra`); índices FGV entram pelo espelho no SGS |
| Operação | cron (coleta horária), bot Telegram como serviço systemd de usuário, deploy Vercel por push |
| Tracking no site | GA4, Google AdSense e Meta Pixel em `site/src/layouts/BaseLayout.astro` |

## 4. Estrutura

```
pyproject.toml, uv.lock, .python-version   # ambiente Python (uv); o .venv não entra no git
pipeline/
  connectors/   # bcb.py, ibge_sidra.py (plugins; registry em __init__.py)
  core/         # scheduler (coleta), aggregations, builder (build+deploy), charts, release_calendar, cron, wage
  db/           # connection.py + migrations/NNN_*.sql (versionadas, idempotentes)
  bot/          # bot Telegram (handlers, notifications)
  gsc/          # coleta e relatório do Google Search Console
  config.py, config_groups.py (grupos curados de /comparar/), cli.py
  */tests/      # testes ficam junto de cada módulo
site/           # Astro: src/pages, src/components/{domain,layout,ui}, src/lib, data/ (JSONs gerados), public/charts/ (PNGs gerados)
data/           # indicadores.db (versionado)
scripts/        # setup, cron/systemd, inspect-db, validações, debug/ (reprodução de conectores)
docs/           # PROJECT-CONTEXT.md, specs por fase (fase-0N/), ROADMAP.md, SEO.md, gsc/
```

## 5. Comandos

```bash
# Setup
bash scripts/setup.sh                              # uv python 3.14 + uv sync + pnpm install
make install                                       # equivalente
uv sync                                            # só o ambiente Python, a partir do uv.lock

# Pipeline (sempre da raiz)
.venv/bin/python -m pipeline.cli status            # diagnóstico
.venv/bin/python -m pipeline.cli migrate           # aplica migrations pendentes
.venv/bin/python -m pipeline.cli collect <CODE>    # coleta um indicador (ou --all)
.venv/bin/python -m pipeline.cli backfill <CODE>   # série histórica completa
.venv/bin/python -m pipeline.cli build             # gera site/data/*.json e site/public/charts/*.png
.venv/bin/python -m pipeline.cli deploy            # git add + commit + push dos artefatos (dispara deploy!)
.venv/bin/python -m pipeline.cli publish           # build + deploy (dispara deploy!)
.venv/bin/python -m pipeline.cli scheduled-collect # o que o cron chama de hora em hora
.venv/bin/python -m pipeline.cli calendar-refresh  # datas oficiais de divulgação (IBGE)
.venv/bin/python -m pipeline.cli gsc-collect|gsc-report|gsc-sites

# Site
cd site && pnpm dev            # http://localhost:4321
cd site && pnpm build
cd site && pnpm astro check    # type check

# Qualidade
.venv/bin/ruff check pipeline/
.venv/bin/pytest pipeline/ -q
bash scripts/validate-fase2-build.sh   # artefatos esperados do build
bash scripts/precommit.sh              # ruff + validate + astro check
```

`deploy` e `publish` fazem `git push` e publicam o site em produção: só execute quando pedido.

## 6. Banco de dados

- Tabelas: `indicators`, `indicator_values`, `collection_logs`, `build_logs`, `schedule_overrides`,
  `release_dates`, `_migrations`, `gsc_*`.
- Leitura rápida: `bash scripts/inspect-db.sh status|indicators|values <CODE>|errors|builds|schedule`
  (`status` usa o Python do venv; os demais exigem o CLI `sqlite3`). Alternativa sem dependências:
  `.venv/bin/python -c "import sqlite3; c=sqlite3.connect('file:data/indicadores.db?mode=ro', uri=True); ..."`.
- **Escrita só via migration** em `pipeline/db/migrations/NNN_*.sql` (numeração sequencial,
  `INSERT OR IGNORE`/idempotente, UUID fixo). Nunca edite dados à mão nem altere schema fora de migration.
- O bot aplica migrations pendentes no startup e no `/coletar all`.

## 7. Operação (como roda em produção)

- Host: desktop Windows 11 + WSL2 (Ubuntu 26.04), não um servidor. O WSL só sobe após o logon no Windows.
- **cron** (usuário): `scheduled-collect` a cada hora cheia + `gsc-collect`/`gsc-report` às segundas 08h.
  O `scheduled-collect` coleta quando o horário agendado mais recente (expressão em `schedule_overrides`,
  hoje `0 7 * * *`) ainda não rodou (`is_due` em `pipeline/core/cron.py`). Se o PC estava desligado às 07h,
  a coleta acontece na primeira hora cheia depois do logon. Horário muda pelo bot (`/agendar`), nunca editando o crontab.
- O deploy commita só `site/data`, `site/public/charts` e `data/indicadores.db` e faz push para o upstream da
  branch (remote `fabioadr`).
- **Bot Telegram**: serviço `indicadores-bot` (`systemctl --user status indicadores-bot`). Comandos:
  `/status /coletar /publicar /indicadores /erros /logs /agendamento /agendar /pausar /retomar /migrar`.
- Coleta → build → deploy (push) → Vercel publica. Erros notificam no Telegram.

## 8. Convenções

- Commits: Conventional Commits, como no histórico (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`),
  escopo opcional (`feat(site): ...`, escopos usuais: `pipeline`, `connectors`, `db`, `bot`, `site`, `gsc`, `infra`).
  `data: update <CODES> (<data>)` é gerado pelo pipeline: não use esse prefixo à mão.
- Python: type hints em tudo, dataclasses em vez de dicts internos, f-strings, `pathlib.Path`,
  docstrings só quando a intenção não é óbvia, testes em `<módulo>/tests/`.
- TypeScript/Astro: `strict`, componentes `.astro` (sem React/Vue/Svelte), Tailwind utility-first,
  JS no cliente mínimo e justificado por feature (orçamento ~5KB gzipped), HTML funcional sem JS.
- Código, nomes e comentários em inglês; conteúdo do site e docs em português.

## 9. Não fazer

- Não introduzir dependência sem justificar (custo, tamanho, alternativa nativa).
- Não converter o site em SSR/SPA nem adicionar framework JS no cliente.
- Não inventar séries/tabelas: confirme `series_id` (SGS) ou `tabela/variavel` (SIDRA) na API oficial antes.
- Não liberar comparações livres em `/comparar/`: só grupos curados em `pipeline/config_groups.py`.
- Não persistir estimativas em `release_dates` (só datas oficiais) nem fazer chamada de rede no `build`.
- Não mexer em tracking (GA4/AdSense/Pixel) sem pedido explícito: priorize precisão e consentimento.
- Não commitar, fazer push, `deploy`/`publish` ou apagar arquivos sem pedido explícito.

## 10. Antes de dizer que terminou

1. `.venv/bin/ruff check pipeline/` nos arquivos alterados e `.venv/bin/pytest pipeline/ -q`.
2. Se mexeu no site: `cd site && pnpm astro check` (e `pnpm build` se mudou rotas/dados).
3. Se mexeu no build: `.venv/bin/python -m pipeline.cli build` + `bash scripts/validate-fase2-build.sh`.
4. Se mexeu em código: `graphify update .` (ver seção 12).

## 11. Workflows (runbooks)

Passo a passo das tarefas recorrentes. Estão no formato de skill do Claude Code, mas são Markdown
comum: qualquer agente pode ler e seguir.

| Tarefa | Runbook |
|---|---|
| Adicionar indicador | `.claude/skills/add-indicator/SKILL.md` |
| Adicionar grupo de comparação | `.claude/skills/add-comparison-group/SKILL.md` |
| Investigar erro de coleta | `.claude/skills/debug-collection/SKILL.md` (scripts em `scripts/debug/`) |
| Checagem antes de commit/push | `.claude/skills/release-check/SKILL.md` |
| Smoke test de milestone | `.claude/skills/smoke-test-milestone/SKILL.md` |

Mais contexto (decisões por área, catálogo de indicadores, status das fases): `docs/PROJECT-CONTEXT.md`.

## 12. graphify

Existe um grafo de conhecimento do código em `graphify-out/`.

- Antes de responder perguntas de arquitetura, leia `graphify-out/GRAPH_REPORT.md`
  (ou navegue `graphify-out/wiki/index.md`, se existir).
- Para "como X se relaciona com Y", prefira `graphify query "<pergunta>"`, `graphify path "<A>" "<B>"`
  ou `graphify explain "<conceito>"` em vez de grep.
- Depois de alterar código, rode `graphify update .` (só AST, sem custo de API).
