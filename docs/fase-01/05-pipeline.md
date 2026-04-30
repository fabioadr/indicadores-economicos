# 05 — Pipeline

## Componentes

```
pipeline/core/
├── scheduler.py       # decide o que coletar e orquestra
├── aggregations.py    # YTD, last_12m, last_24m, since_inception
├── builder.py         # gera JSONs + PNGs + git push
└── charts.py          # gera PNG via matplotlib
```

## CLI

Entry point único: `pipeline/cli.py`. Uso (via `python -m pipeline.cli <command>`):

| Comando | Ação |
|---|---|
| `migrate` | Aplica migrations pendentes |
| `collect --all` | Roda scheduler em todos os indicadores ativos |
| `collect <code>` | Coleta um indicador específico (ignora regra de frequência) |
| `backfill <code>` | Coleta histórico inteiro de um indicador (sobrescreve) |
| `build` | Gera JSONs + PNGs (sem git push) |
| `deploy` | git add + commit + push |
| `publish` | `build` + `deploy` em sequência |
| `status` | Mostra resumo: indicadores, últimas coletas, último build |

## Scheduler

### Lógica de decisão

Para cada indicador ativo, decide se deve coletar agora:

```python
def should_collect(indicator) -> bool:
    if not indicator.last_collected_at:
        return True  # nunca coletado
    last = parse_iso(indicator.last_collected_at)
    now = datetime.now()
    elapsed_hours = (now - last).total_seconds() / 3600

    if indicator.frequency == "daily":
        return elapsed_hours >= 20  # coletar 1x/dia com folga
    if indicator.frequency == "biweekly":
        return elapsed_hours >= 24 * 14
    if indicator.frequency == "monthly":
        # tenta diariamente após o expected_release_day até achar dado novo
        if elapsed_hours < 24:
            return False
        # se já temos o valor do mês passado, não precisa
        if has_value_for_month(indicator, last_month()):
            return elapsed_hours >= 24 * 28  # próximo mês
        return True
    raise ValueError(f"Frequência desconhecida: {indicator.frequency}")
```

### Execução

```python
def run_all(triggered_by: str = "cron"):
    indicators = db.list_active_indicators()
    results = []
    for ind in indicators:
        if not should_collect(ind):
            log_skipped(ind, triggered_by)
            continue
        result = collect_single(ind, triggered_by)
        results.append(result)
    return results

def collect_single(ind, triggered_by):
    log = start_log(ind, triggered_by)
    try:
        connector = get_connector(ind.connector_type)
        config = json.loads(ind.connector_config)
        # Coleta apenas dados novos (a partir do último valor + 1 mês)
        last_value_date = db.get_last_value_date(ind.id)
        since = (last_value_date + relativedelta(months=1)) if last_value_date else None
        points = connector.fetch(config, since=since)

        added = 0
        updated = 0
        for p in points:
            existed = db.upsert_value(ind.id, p)
            if existed:
                updated += 1
            else:
                added += 1

        if added or updated:
            recompute_aggregations(ind.id)
            db.update_indicator(ind.id, last_collected_at=now_iso())

        finish_log(log, status="success", added=added, updated=updated)
        return CollectResult(ind, added, updated, error=None)
    except Exception as e:
        finish_log(log, status="error", error=str(e))
        bot.notify_error(ind, e)
        return CollectResult(ind, 0, 0, error=e)
```

## Agregações

```python
# pipeline/core/aggregations.py
def recompute_aggregations(indicator_id: str):
    """Recalcula YTD, last_12m, last_24m, since_inception para todos os valores."""
    values = db.list_values(indicator_id, order="asc")  # ordenado por reference_date asc
    if not values:
        return

    inception_factor = 1.0  # produto cumulativo desde o início
    by_year: dict[int, list[float]] = {}

    updates = []
    for i, v in enumerate(values):
        # since_inception
        inception_factor *= (1 + v.value / 100)
        since_inception = (inception_factor - 1) * 100

        # YTD
        year = parse_date(v.reference_date).year
        by_year.setdefault(year, []).append(v.value)
        ytd = accumulate(by_year[year])

        # last_12m
        last_12 = values[max(0, i - 11) : i + 1]  # janela inclusive
        last_12m = accumulate([x.value for x in last_12]) if len(last_12) == 12 else None

        # last_24m
        last_24 = values[max(0, i - 23) : i + 1]
        last_24m = accumulate([x.value for x in last_24]) if len(last_24) == 24 else None

        updates.append((v.id, ytd, last_12m, last_24m, since_inception))

    db.batch_update_aggregations(updates)


def accumulate(percentages: list[float]) -> float:
    factor = 1.0
    for p in percentages:
        factor *= (1 + p / 100)
    return (factor - 1) * 100
```

**Observações:**

- Recomputa série inteira do indicador a cada coleta. Trivial em termos de performance (até ~5000 linhas em milissegundos).
- Para `last_12m`/`last_24m`, retorna `NULL` se não houver janela completa.
- Para `since_inception`, sempre tem valor (1+ leituras = válido).

## Builder

### O que gera

Para cada execução de build:

```
site/data/
├── indicators.json     # metadata de todos os ativos (para home, navegação)
├── ipca.json           # série completa + agregações + descrição
├── cdi.json
└── tr.json

site/public/charts/
├── ipca-2026.png       # gráfico do ano corrente
├── ipca-history.png    # gráfico de toda a série
├── cdi-2026.png
├── cdi-history.png
├── tr-2026.png
└── tr-history.png
```

### Estrutura dos JSONs

**`indicators.json`** (índice geral):

```json
{
  "generated_at": "2026-04-28T10:15:00-03:00",
  "categories": {
    "inflacao": {
      "label": "Inflação",
      "indicators": ["ipca"]
    },
    "juros": {
      "label": "Juros",
      "indicators": ["cdi"]
    },
    "correcao_monetaria": {
      "label": "Correção Monetária",
      "indicators": ["tr"]
    }
  },
  "indicators": [
    {
      "code": "IPCA",
      "slug": "ipca",
      "name": "IPCA - Índice de Preços ao Consumidor Amplo",
      "category": "inflacao",
      "frequency": "monthly",
      "latest": {
        "reference_date": "2026-03-01",
        "value": 0.56,
        "ytd": 1.42,
        "last_12m": 4.83
      }
    }
    /* ... */
  ]
}
```

**`{slug}.json`** (página de detalhe):

```json
{
  "code": "IPCA",
  "slug": "ipca",
  "name": "IPCA - Índice de Preços ao Consumidor Amplo",
  "short_description": "Indicador oficial de inflação do Brasil, calculado pelo IBGE.",
  "long_description": "## O que é o IPCA?\n\nO IPCA — Índice...",
  "category": "inflacao",
  "unit": "percent",
  "frequency": "monthly",
  "source": {
    "name": "Banco Central do Brasil",
    "url": "https://www.bcb.gov.br/..."
  },
  "meta": {
    "title": "IPCA - Tabela atualizada março/2026 | Indicadores Econômicos Hoje",
    "description": "IPCA de março/2026: 0,56%. Acumulado 12 meses: 4,83%. Tabela histórica completa desde 1980."
  },
  "latest": {
    "reference_date": "2026-03-01",
    "value": 0.56,
    "ytd": 1.42,
    "last_12m": 4.83,
    "last_24m": 9.21
  },
  "values": [
    {
      "reference_date": "1980-01-01",
      "value": 6.62,
      "ytd": 6.62,
      "last_12m": null,
      "last_24m": null,
      "since_inception": 6.62
    }
    /* ... ordenado por reference_date asc */
  ],
  "charts": {
    "current_year": "/charts/ipca-2026.png",
    "history": "/charts/ipca-history.png"
  },
  "last_built_at": "2026-04-28T10:15:00-03:00"
}
```

### Pipeline de build

```python
def build():
    indicators = db.list_active_indicators()
    if not indicators:
        return BuildResult(status="no_changes")

    # Detecta se há indicadores com dados novos desde o último build
    last_build = db.get_last_successful_build()
    changed = [i for i in indicators if needs_rebuild(i, last_build)]

    if not changed and last_build:
        log_build(status="no_changes", indicators=[])
        return BuildResult(status="no_changes")

    # Gera JSONs (sempre todos, é barato)
    write_indicators_index(indicators)
    for ind in indicators:
        write_indicator_detail(ind)

    # Gera charts apenas para os que mudaram
    for ind in changed:
        generate_chart_current_year(ind)
        generate_chart_history(ind)

    db.update_indicators_last_built(changed, now_iso())
    log = log_build(status="success", indicators=[i.code for i in changed])
    return BuildResult(status="success", changed=changed, log_id=log.id)


def deploy(build_log_id: str):
    """git add + commit + push."""
    repo_path = config.GITHUB_REPO_PATH
    files_changed = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True).stdout
    if not files_changed.strip():
        return DeployResult(status="no_changes")

    subprocess.run(["git", "-C", repo_path, "add", "site/data/", "site/public/charts/", "data/indicadores.db"], check=True)
    msg = build_commit_message(build_log_id)
    subprocess.run(["git", "-C", repo_path, "commit", "-m", msg], check=True)
    subprocess.run(["git", "-C", repo_path, "push", "origin", "main"], check=True)
    sha = subprocess.run(["git", "-C", repo_path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    db.update_build_log(build_log_id, git_commit_sha=sha)
    return DeployResult(status="success", commit_sha=sha)
```

### Mensagem de commit

```
data: update IPCA, CDI (2026-04-28)

Updated indicators:
- IPCA: 1 new value (2026-03-01: 0.56%)
- CDI: 1 new value (2026-03-01: 0.93%)

Build log: <id>
```

## Charts

Implementados em `pipeline/core/charts.py` usando matplotlib.

### Convenções visuais

- Tamanho: 1200×600px @ 100 dpi (good for retina)
- Background: branco (combina com qualquer tema do site)
- Sem grid pesado — apenas linhas horizontais sutis
- Fonte: matplotlib default (DejaVu Sans) é suficiente
- Cores: paleta única definida em `charts.py` constante `PALETTE`
- Nada de seaborn (uma dependência a menos)

### Tipos

1. **`{slug}-{year}.png`** — barras mensais do ano corrente + linha de acumulado YTD
2. **`{slug}-history.png`** — linha mensal de toda a série + linha de acumulado 12m

## Logs

- Stdout para tudo (Python `logging` configurado em `pipeline/config.py`)
- Tee para arquivo `pipeline/logs/{YYYY-MM-DD}.log`
- Logrotate via cron diário (`logrotate -f /etc/logrotate.d/indicadores`)

## Tratamento de erros e idempotência

- `upsert_value` usa `INSERT ... ON CONFLICT DO UPDATE` (sem race, sem dup)
- Reexecutar `collect` é seguro — só insere o que falta, atualiza valores que mudaram
- Reexecutar `build` é seguro — sobrescreve JSONs e PNGs
- Reexecutar `deploy` é seguro — se nada mudou no git, é no-op
- Erro em um indicador não interrompe a coleta dos outros
- Bot é notificado para qualquer erro de coleta ou build
