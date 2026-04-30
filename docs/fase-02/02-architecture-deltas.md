# 02 — Deltas de Arquitetura

> Mudanças e adições na arquitetura da Fase 1. Tudo que **não** está aqui permanece igual.

## Visão geral das mudanças

```
                                ┌───────────────────────┐
                                │  Pipeline (Python)    │
                                │                       │
   [novo]   IBGE SIDRA  ───────►│  connectors/          │
            connector            │  ├── bcb.py [já existe]│
                                │  └── ibge_sidra.py    │
                                │                       │
   [adições]                    │  core/charts.py       │
   indicators_groups            │  ├── chart por indicador (já existe)│
   (configuração)               │  └── chart de comparação [novo]│
                                │                       │
                                │  bot/handlers.py      │
   [novo]                       │  ├── /agendamento     │
   schedule_overrides           │  └── /pausar          │
   (tabela DB)                  └───────────────────────┘
                                            │
                                            ▼
                                ┌───────────────────────┐
                                │   Site (Astro)        │
                                │                       │
   [novo arquivo]               │  data/                │
   site/data/groups.json        │  └── groups.json [novo]│
                                │                       │
   [novas páginas]              │  pages/               │
                                │  ├── comparar/        │
                                │  │   ├── index.astro [novo]│
                                │  │   └── [slug].astro [novo]│
                                │  └── construcao-civil/ [novo]│
                                │                       │
   [Astro Islands]              │  components/          │
                                │  ├── PeriodFilter.astro+ts [novo]│
                                │  └── YearSelector.astro+ts [novo]│
                                └───────────────────────┘
```

## Mudanças no pipeline

### 1. Novo conector: IBGE SIDRA

Implementação em `pipeline/connectors/ibge_sidra.py`. Especificação completa em `03-connectors.md`. Registrado como `ibge_sidra` no registry; usado quando `indicator.connector_type = "ibge_sidra"`.

### 2. Geração de charts comparativos

Novo módulo: `pipeline/core/comparison_charts.py`.

Recebe configuração de grupo (de `pipeline/config/indicator_groups.py`) e gera 1 PNG por grupo, comparando `last_12m` ao longo do tempo dos indicadores listados.

Saída: `site/public/charts/compare-{slug-do-grupo}.png`.

Triggered no comando `pipeline.cli build`, depois da geração dos PNGs individuais.

### 3. Novo módulo de configuração de grupos

`pipeline/config/indicator_groups.py`:

```python
INDICATOR_GROUPS = [
    {
        "slug": "inflacao-oficial",
        "title": "Inflação no Brasil: IPCA, IGP-M e INPC",
        "description": "Os três principais índices de inflação brasileira lado a lado.",
        "indicators": ["IPCA", "IGPM", "INPC"],
        "metric": "last_12m",
    },
    {
        "slug": "indices-fgv",
        "title": "Índices da FGV: IGP-M e IGP-DI",
        "description": "Comparação entre os dois índices gerais de preços da FGV.",
        "indicators": ["IGPM", "IGPDI"],
        "metric": "last_12m",
    },
    {
        "slug": "juros-vs-inflacao",
        "title": "Juros vs Inflação: SELIC e IPCA",
        "description": "Como a SELIC se move em relação à inflação oficial.",
        "indicators": ["SELIC", "IPCA"],
        "metric": "last_12m",
    },
    {
        "slug": "construcao-civil",
        "title": "Construção Civil: INCC-M e IGP-M",
        "description": "Custos da construção civil comparados ao índice geral de preços.",
        "indicators": ["INCCM", "IGPM"],
        "metric": "last_12m",
    },
]
```

A lista é versionada no código (não vai ao DB). Adicionar/remover grupos é uma alteração simples + redeploy.

### 4. Tabela nova no DB: `schedule_overrides`

Permite ao bot Telegram alterar o agendamento sem editar crontab. Especificação em `06-telegram-improvements.md`.

```sql
CREATE TABLE schedule_overrides (
    id              TEXT PRIMARY KEY,
    cron_expression TEXT NOT NULL,        -- ex: "0 7 * * *"
    enabled         INTEGER NOT NULL DEFAULT 1,
    last_run_at     TEXT,
    next_run_at     TEXT,
    description     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Apenas uma linha ativa por vez (semanticamente; sem constraint dura). O cron real continua chamando `pipeline.cli scheduled-collect`, que consulta a tabela e decide se executa.

### 5. Novo comando CLI: `scheduled-collect`

```
python -m pipeline.cli scheduled-collect
```

Executa coleta apenas se a configuração ativa em `schedule_overrides` permite a hora atual (avalia a cron expression). Substitui `collect --all` na entrada do crontab.

Permite que o cron rode de hora em hora, e o pipeline decida internamente se deve agir, baseado na config dinâmica.

## Mudanças no site

### 1. JS no cliente: Astro Islands

A Fase 1 era 100% estática. A Fase 2 introduz JS **apenas** para:

- `components/PeriodFilter.astro` — botões "12m / 24m / 5a / Total" que filtram a tabela cliente-side
- `components/YearSelector.astro` — dropdown para escolher ano específico na tabela histórica

Implementação: vanilla JS direto no `<script>` do componente Astro (sem framework). Hidratação `client:idle` (carrega após resto da página).

Tamanho-alvo: **< 5KB gzipped** combinado.

### 2. Novas rotas

```
/comparar/                      Lista de comparações curadas
/comparar/{slug-do-grupo}/      Página de cada comparação
/construcao-civil/              Categoria nova (apenas INCC-M na Fase 2)
/selic/, /igp-m/, /igp-di/,
/inpc/, /incc-m/, /ipca-15/     Detalhes dos novos indicadores
```

### 3. Novo arquivo: `site/data/groups.json`

Gerado pelo pipeline (no build), consumido pelo Astro:

```json
{
  "generated_at": "2026-04-28T10:15:00-03:00",
  "groups": [
    {
      "slug": "inflacao-oficial",
      "title": "Inflação no Brasil: IPCA, IGP-M e INPC",
      "description": "Os três principais índices de inflação brasileira lado a lado.",
      "indicators": [
        {"code": "IPCA", "slug": "ipca", "name": "..."},
        {"code": "IGPM", "slug": "igp-m", "name": "..."},
        {"code": "INPC", "slug": "inpc", "name": "..."}
      ],
      "chart": "/charts/compare-inflacao-oficial.png",
      "latest": {
        "reference_date": "2026-03-01",
        "values": {
          "IPCA": {"value": 0.56, "last_12m": 4.83},
          "IGPM": {"value": 0.21, "last_12m": 2.91},
          "INPC": {"value": 0.51, "last_12m": 4.62}
        }
      }
    }
  ]
}
```

## Mudanças no banco de dados

| Mudança | Tipo | Migration |
|---|---|---|
| Tabela `schedule_overrides` | Nova | 003_schedule_overrides.sql |
| Linha default de schedule (07:00 daily) | Seed | 003 |
| Categoria `construcao_civil` (string em uso) | Convenção | — |
| Seeds dos 6 novos indicadores | Seed | 004_seed_phase2_indicators.sql |

Schema de `indicators` e `indicator_values` **não muda**.

## Mudanças no bot

Comandos novos:

| Comando | Função |
|---|---|
| `/agendamento` | Mostra agendamento atual |
| `/agendar <cron>` | Define novo cron, valida sintaxe |
| `/pausar` | Desativa coleta automática |
| `/retomar` | Reativa coleta automática |
| `/grupos` | Lista grupos de comparação |

Detalhes em `06-telegram-improvements.md`.

## O que NÃO muda

- Stack: Python 3.12, SQLite, Astro 4, Tailwind, Vercel
- Plugin pattern dos conectores
- Estrutura de diretórios (apenas adições)
- Schema de `indicators`, `indicator_values`, `collection_logs`, `build_logs`
- Formato e estrutura dos JSONs por indicador (`{slug}.json`)
- Estilo visual (paleta, tipografia)
- Estratégia de deploy (git push → Vercel)
- Estrutura do crontab (mas o comando muda de `collect --all` para `scheduled-collect`)

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Mudança no SIDRA quebra coleta | Tests unitários do conector com fixtures; alarme via bot |
| JS no cliente compromete performance | Budget rígido <5KB; CI checa tamanho do bundle |
| Comparações ficam desatualizadas | PNGs regenerados a cada build, junto com os individuais |
| `schedule_overrides` mal configurado paralisa coleta | `/status` do bot indica quando próxima coleta vai rodar; comando `/coletar all` continua funcionando independente do agendamento |
