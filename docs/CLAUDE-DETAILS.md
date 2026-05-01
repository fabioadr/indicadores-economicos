## O projeto

**Indicadores Econômicos Hoje** é um agregador estático de indicadores econômicos brasileiros, com pipeline local de coleta automatizada e publicação via Vercel.

- **Site público**: https://indicadoreseconomicoshoje.com.br
- **Stack site**: Astro + Tailwind, 100% estático
- **Stack pipeline**: Python 3.12 + SQLite, roda em notebook Ubuntu local
- **Operação**: cron + Telegram bot

Antes de qualquer trabalho, leia `docs/00-README.md` e os documentos relevantes ao escopo da tarefa.

## Diretrizes gerais

### Filosofia

- **Static-first**: o site é HTML estático, sem runtime, sem banco em produção
- **SQLite local é a single source of truth**; JSONs e PNGs são derivações versionadas
- **Idempotência em tudo**: qualquer comando deve poder ser re-executado sem efeito colateral
- **Fail loud**: erros viram notificação Telegram imediata, nunca silenciosos
- **Plugin pattern**: novos conectores não tocam o core
- **Sem over-engineering**: 4 tabelas, 3 indicadores, 1 fonte. Simplicidade vence

### Stack — escolhas firmes (não desviar sem combinar)

- Python 3.12+, sem ORM (sqlite3 puro com helper)
- httpx (não requests), respx para mocks de teste
- python-telegram-bot v21+ (async)
- Astro 4+, Tailwind 3+
- Sem Docker, sem n8n, sem Next.js, sem PostgreSQL
- Matplotlib para PNGs (não seaborn)

### Estilo de código

**Python:**

- Type hints em tudo
- Dataclasses ao invés de dicts internos
- f-strings, nunca `.format()` ou `%`
- `pathlib.Path`, nunca `os.path`
- Docstrings só onde a intenção não é óbvia
- Testes com pytest, organizados em `tests/` por módulo
- Linting: ruff (config padrão)

**TypeScript / Astro:**

- TypeScript estrito (`strict: true`)
- Componentes Astro `.astro` para layout, sem React/Vue
- Tailwind utility-first, sem CSS custom exceto vars no `:root`

### Convenções de commit

`<scope>: <descrição imperativa>`

Scopes: `pipeline`, `connectors`, `db`, `bot`, `site`, `docs`, `infra`, `data`

Exemplos:

- `connectors: add BCB SGS connector with pagination`
- `data: update IPCA, CDI (2026-04-28)` (auto-gerado pelo pipeline)
- `site: add JSON-LD Dataset schema to indicator pages`

### Estrutura de diretórios

```
pipeline/        # sistema Python local
site/            # site Astro
data/            # SQLite (versionado)
docs/            # specs (incluindo este projeto)
scripts/         # bash auxiliares
```

Detalhes em `docs/02-architecture.md`.

## Comandos comuns

```bash
# Setup inicial
make install                          # cria venv + instala deps + pnpm install

# Desenvolvimento
python -m pipeline.cli migrate        # aplica migrations
python -m pipeline.cli backfill IPCA  # backfill histórico
python -m pipeline.cli collect --all  # coleta scheduled
python -m pipeline.cli build          # gera JSON+PNG
python -m pipeline.cli publish        # build + git push

cd site && pnpm dev                   # dev server Astro (porta 4321)
cd site && pnpm build                 # build de produção
cd site && pnpm preview               # preview do build

# Testes
pytest pipeline/                      # testes Python
cd site && pnpm check                 # type check Astro

# Bot (em foreground para debug)
python -m pipeline.bot

# Logs
tail -f pipeline/logs/$(date +%Y-%m-%d).log
```

## Variáveis de ambiente

Em `pipeline/.env` (nunca commitar; ver `pipeline/.env.example`):

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GITHUB_REPO_PATH=/home/<user>/indicadoreseconomicos
DB_PATH=./data/indicadores.db
SITE_DATA_DIR=./site/data
SITE_CHARTS_DIR=./site/public/charts
LOG_LEVEL=INFO
```

## Coisas a NÃO fazer

- ❌ Não introduzir novas dependências sem necessidade clara
- ❌ Não converter o site em SSR/SPA
- ❌ Não adicionar tracking analytics na Fase 1 (sem GA, sem Hotjar, sem Meta Pixel)
- ❌ Não inventar endpoints novos no SGS — apenas séries documentadas
- ❌ Não armazenar credenciais em código nem em SQL
- ❌ Não fazer commits silenciosos de `.env` (proteção via `.gitignore`)
- ❌ Não usar emojis no código (apenas em strings de UI/Telegram quando fizerem sentido)
- ❌ Não editar dados manualmente no SQLite — sempre via pipeline ou migration

## Quando estiver em dúvida

1. Re-ler `docs/02-architecture.md` e `docs/09-implementation-plan.md`
2. Se a dúvida envolve uma decisão arquitetural não coberta, **perguntar** antes de implementar
3. Se for detalhe de implementação, escolher a opção mais simples e documentar

## Indicadores Fase 1

| Code | Slug | Categoria          | Fonte | Série SGS |
| ---- | ---- | ------------------ | ----- | --------- |
| IPCA | ipca | inflacao           | BCB   | 433       |
| CDI  | cdi  | juros              | BCB   | 4391      |
| TR   | tr   | correcao_monetaria | BCB   | 226       |

Detalhes completos em `docs/08-indicators-catalog.md`.

## Fase 2 — Adições e ajustes

A Fase 2 está descrita em `docs/fase2/`. Antes de qualquer trabalho relacionado, leia `docs/fase2/00-README.md` e os docs específicos do escopo.

### Indicadores adicionais

| Code   | Slug    | Categoria        | Conector   | Config                    |
| ------ | ------- | ---------------- | ---------- | ------------------------- |
| SELIC  | selic   | juros            | bcb_sgs    | series_id 4189            |
| IGPM   | igp-m   | inflacao         | bcb_sgs    | series_id 189             |
| IGPDI  | igp-di  | inflacao         | bcb_sgs    | series_id 190             |
| INPC   | inpc    | inflacao         | bcb_sgs    | series_id 188             |
| INCCM  | incc-m  | construcao_civil | bcb_sgs    | series_id 192             |
| IPCA15 | ipca-15 | inflacao         | ibge_sidra | tabela 7060, variavel 355 |

Detalhes completos em `docs/fase2/04-indicators-catalog.md`.

### Conector novo: IBGE SIDRA

Implementado em `pipeline/connectors/ibge_sidra.py`. Registry name: `ibge_sidra`.

Para mapear novos indicadores IBGE, use o subagent `sidra-research` (não inventar tabela/variavel sem validar contra `https://sidra.ibge.gov.br/`).

### Categoria nova: `construcao_civil`

URL: `/construcao-civil/`. Apenas INCC-M na Fase 2; receberá outros indicadores em fases futuras.

### JS no cliente: política revisada

A regra "zero JS" da Fase 1 passa a ser **"JS mínimo no cliente, justificado por feature, sem framework"**. Permitido:

- Filtros de período de tabela (Astro Islands com vanilla TS)
- Persistência em `localStorage` para preferências de UI

Não permitido:

- Frameworks (React/Vue/Svelte) no cliente — manter Astro puro
- Bundle gzipped acima de 5KB total
- JS para conteúdo principal (HTML deve continuar funcional sem JS)

### Página nova: `/comparar/`

Comparações pré-renderizadas em PNG, configuradas em `pipeline/config/indicator_groups.py`. Adicionar/remover grupos é uma alteração de código + redeploy.

Para adicionar novos grupos, use a skill `add-comparison-group`.

### Agendamento configurável

Crontab da Fase 2 chama `pipeline.cli scheduled-collect` de hora em hora. O comando consulta `schedule_overrides` no DB e decide se executa.

Operação via Telegram: `/agendamento`, `/agendar <cron>`, `/pausar`, `/retomar`.

**Não editar o crontab manualmente para alterar horário** — usar `/agendar` no Telegram.

### Comandos comuns adicionados

```bash
# Coleta gateada por agendamento (substitui collect --all no cron)
python -m pipeline.cli scheduled-collect

# Forçar regeneração apenas das comparações (pula coleta + indicadores individuais)
bash scripts/regenerate-comparisons.sh

# Validação estendida (Fase 1 + Fase 2)
bash scripts/validate-fase2-build.sh
```

### Dependências adicionadas

Em `pipeline/requirements.txt`:

```
croniter
```

Em `site/package.json`: nada novo (Astro Islands é nativo).

### Coisas a NÃO fazer (adendos)

- ❌ Não migrar IPCA da Fase 1 para SIDRA — é decisão explícita de não fazer agora
- ❌ Não construir conector FGV nativo na Fase 2 — usar BCB SGS como espelho
- ❌ Não introduzir frameworks JS no cliente — manter Astro Islands com vanilla TS
- ❌ Não permitir comparações combinatórias livres — apenas grupos curados, pré-renderizados
- ❌ Não permitir frequência de cron acima de 1x/hora via `/agendar`

### Quando estiver em dúvida (ajuste ao da Fase 1)

Antes de implementar features de Fase 2, valide nesta ordem:

1. `docs/fase2/01-vision-and-scope.md` — está dentro do escopo?
2. `docs/fase2/02-architecture-deltas.md` — encaixa nos deltas previstos?
3. `docs/fase2/07-implementation-plan.md` — está dentro do milestone certo?
4. Se nenhum dos três cobre, **perguntar antes de implementar**

### Indicadores Fase 2 — referência rápida

| Code   | Série/Tabela   | Inception |
| ------ | -------------- | --------- |
| SELIC  | BCB SGS 4189   | 1986-06   |
| IGPM   | BCB SGS 189    | 1989-06   |
| IGPDI  | BCB SGS 190    | 1944-02   |
| INPC   | BCB SGS 188    | 1979-04   |
| INCCM  | BCB SGS 192    | 1989-06   |
| IPCA15 | SIDRA 7060/355 | 2000-05   |

> Sempre confirmar via subagent (`bcb-research` ou `sidra-research`) antes de aplicar mudanças no DB.
