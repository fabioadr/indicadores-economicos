# 05 — Features de Site da Fase 2

Duas adições no site nesta fase:

1. **Filtros de período na tabela histórica** (Astro Islands com vanilla JS)
2. **Página de comparações** (`/comparar/`) com PNGs comparativos pré-renderizados

---

## Parte A — Filtros de período na tabela histórica

### Comportamento desejado

Em qualquer página de detalhe de indicador (ex: `/ipca/`), a tabela histórica passa a ter um seletor de período acima dela:

```
┌────────────────────────────────────────┐
│  [12m] [24m] [5 anos] [10 anos] [Tudo] │   ← seletor (segmented control)
├────────────────────────────────────────┤
│  Período   │ Valor │ YTD   │ 12m       │
├────────────┼───────┼───────┼───────────┤
│  mar/2026  │ 0,56% │ 1,42% │ 4,83%     │
│  fev/2026  │ 0,52% │ 0,86% │ 4,76%     │
│   ...                                   │
└────────────────────────────────────────┘
```

Default: **12 meses**. Ao clicar em outra opção, a tabela filtra cliente-side (sem reload). A escolha persiste em `localStorage` por slug.

### Por que cliente-side

Os dados completos da série já estão no JSON consumido pela página (`site/data/{slug}.json`). Filtrar é UI puro — exigir o servidor seria desnecessário.

### Componente

`site/src/components/PeriodFilter.astro`:

```astro
---
// Props
interface Props {
  slug: string;        // identifica o filtro no localStorage
  totalRows: number;   // total de linhas; usado em "Tudo"
}
const { slug, totalRows } = Astro.props;
---

<div class="period-filter" data-slug={slug} data-total={totalRows}>
  <button data-period="12" class="active" type="button">12 meses</button>
  <button data-period="24" type="button">24 meses</button>
  <button data-period="60" type="button">5 anos</button>
  <button data-period="120" type="button">10 anos</button>
  <button data-period="all" type="button">Tudo</button>
</div>

<script>
  const STORAGE_PREFIX = 'period-filter:';

  document.querySelectorAll<HTMLDivElement>('.period-filter').forEach((root) => {
    const slug = root.dataset.slug!;
    const total = parseInt(root.dataset.total!, 10);
    const buttons = root.querySelectorAll<HTMLButtonElement>('button');
    const tableId = `history-table-${slug}`;
    const table = document.getElementById(tableId);
    if (!table) return;

    const stored = localStorage.getItem(STORAGE_PREFIX + slug);
    const initial = stored ?? '12';
    apply(initial);

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const period = btn.dataset.period!;
        localStorage.setItem(STORAGE_PREFIX + slug, period);
        apply(period);
      });
    });

    function apply(period: string) {
      buttons.forEach((b) => {
        b.classList.toggle('active', b.dataset.period === period);
      });
      const limit = period === 'all' ? total : parseInt(period, 10);
      const rows = table!.querySelectorAll<HTMLTableRowElement>('tbody tr');
      // Os últimos N rows (mais recentes) — assumindo ordenação desc na tabela
      rows.forEach((tr, idx) => {
        tr.style.display = idx < limit ? '' : 'none';
      });
    }
  });
</script>

<style>
  .period-filter {
    display: flex;
    gap: 0;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    width: fit-content;
    margin-bottom: 1rem;
  }
  .period-filter button {
    padding: 0.5rem 1rem;
    background: var(--bg-elevated);
    color: var(--ink-muted);
    border: none;
    border-right: 1px solid var(--border);
    cursor: pointer;
    font-family: var(--font-body);
    font-size: 0.875rem;
  }
  .period-filter button:last-child { border-right: none; }
  .period-filter button.active {
    background: var(--ink);
    color: var(--bg-elevated);
  }
  .period-filter button:hover:not(.active) {
    background: var(--bg);
  }
</style>
```

### Ajuste em `IndicatorTableHistory.astro`

A tabela existente da Fase 1 ganha um atributo `id` consistente:

```astro
<table id={`history-table-${slug}`}>
  <!-- ... -->
</table>
```

A tabela continua sendo renderizada cheia no servidor (todos os rows). O filtro só esconde rows com `display: none`. Isso preserva SEO (todos os dados estão no HTML) e funciona sem JS.

### Acessibilidade

- Botões são `<button>` reais (focusables, navegáveis por teclado)
- Estado `aria-pressed` no botão ativo:
  ```ts
  buttons.forEach((b) => {
    const isActive = b.dataset.period === period;
    b.classList.toggle('active', isActive);
    b.setAttribute('aria-pressed', String(isActive));
  });
  ```
- Sem JS, todos os dados continuam visíveis (degradação graceful)

### Tamanho do JS

Inline no `<script>` do componente Astro. Astro 4+ inlina scripts pequenos por padrão, ou agrupa em um único arquivo de bundle se vários componentes usarem. Estimativa: < 1KB minified gzipped.

---

## Parte B — Página de comparações

### Conceito

Nova rota `/comparar/` lista comparações curadas. Cada comparação compara N indicadores afins em um único gráfico PNG.

```
/comparar/                         Lista todas as comparações
/comparar/inflacao-oficial/        IPCA vs IGP-M vs INPC (12m)
/comparar/indices-fgv/             IGP-M vs IGP-DI (12m)
/comparar/juros-vs-inflacao/       SELIC vs IPCA (12m)
/comparar/construcao-civil/        INCC-M vs IGP-M (12m)
```

### Estrutura da página `/comparar/`

```
┌───────────────────────────────────────────┐
│  Comparações                              │
│                                           │
│  ┌───────────────────────────────────────┐│
│  │ [PNG comparativo IPCA/IGPM/INPC]      ││
│  │ Inflação no Brasil: IPCA, IGP-M e INPC││
│  │ Os três principais índices...         ││
│  │ → Ver comparação                      ││
│  └───────────────────────────────────────┘│
│  ┌───────────────────────────────────────┐│
│  │ [PNG comparativo IGPM/IGPDI]          ││
│  │ Índices da FGV: IGP-M e IGP-DI        ││
│  │ ...                                   ││
│  └───────────────────────────────────────┘│
└───────────────────────────────────────────┘
```

### Estrutura da página `/comparar/{slug}/`

```
┌───────────────────────────────────────────┐
│  Inflação no Brasil: IPCA, IGP-M e INPC   │
│  Os três principais índices...            │
│                                           │
│  [PNG grande do gráfico comparativo]      │
│                                           │
│  Valores recentes (acumulado 12 meses)    │
│  ┌──────┬─────────┬─────────┬──────────┐  │
│  │ Mês  │ IPCA    │ IGP-M   │ INPC     │  │
│  ├──────┼─────────┼─────────┼──────────┤  │
│  │ mar  │ 4,83%   │ 2,91%   │ 4,62%    │  │
│  │ fev  │ 4,76%   │ 2,87%   │ 4,55%    │  │
│  └──────┴─────────┴─────────┴──────────┘  │
│                                           │
│  Indicadores incluídos:                   │
│  → IPCA · → IGP-M · → INPC                │
└───────────────────────────────────────────┘
```

### Geração do PNG comparativo

Implementação em `pipeline/core/comparison_charts.py`. Para cada grupo definido em `pipeline/config/indicator_groups.py`:

1. Lê os valores de cada indicador do grupo (filtrando pelo `metric` configurado, default `last_12m`)
2. Toma o intervalo de tempo comum entre eles (interseção das datas)
3. Plota uma linha por indicador, com legenda
4. Salva em `site/public/charts/compare-{slug}.png`

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pipeline.config.indicator_groups import INDICATOR_GROUPS
from pipeline.db import connection as db

PALETTE = ["#1E3A8A", "#B91C1C", "#166534", "#92400E", "#581C87"]

def generate_comparison_chart(group: dict, output_path: str):
    indicators = [db.get_indicator_by_code(c) for c in group["indicators"]]
    metric = group.get("metric", "last_12m")

    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

    for i, ind in enumerate(indicators):
        values = db.list_values(ind.id, order="asc")
        # Filter where metric is not null (rolling windows need history)
        points = [(v.reference_date, getattr(v, metric)) for v in values if getattr(v, metric) is not None]
        if not points:
            continue
        dates, values = zip(*points)
        ax.plot(dates, values, label=ind.code, color=PALETTE[i % len(PALETTE)], linewidth=2)

    ax.set_title(group["title"], fontsize=14, pad=20)
    ax.set_ylabel(metric_label(metric))
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def metric_label(metric: str) -> str:
    return {
        "last_12m": "Acumulado 12 meses (%)",
        "last_24m": "Acumulado 24 meses (%)",
        "value": "Variação mensal (%)",
        "ytd": "Acumulado no ano (%)",
    }.get(metric, metric)
```

### Geração do `groups.json`

Em `pipeline/core/builder.py`, após gerar os JSONs individuais e os charts comparativos:

```python
def write_groups_index(groups: list[dict], output_path: str):
    enriched = []
    for group in groups:
        indicators_full = [db.get_indicator_by_code(c) for c in group["indicators"]]
        latest_values = {}
        # Pega últimos valores do mesmo período (alinha pela data mais recente comum)
        common_date = find_latest_common_date(indicators_full)
        if common_date:
            for ind in indicators_full:
                v = db.get_value(ind.id, common_date)
                if v:
                    latest_values[ind.code] = {"value": v.value, "last_12m": v.last_12m}

        enriched.append({
            "slug": group["slug"],
            "title": group["title"],
            "description": group["description"],
            "metric": group.get("metric", "last_12m"),
            "indicators": [
                {"code": i.code, "slug": i.slug, "name": i.name}
                for i in indicators_full
            ],
            "chart": f"/charts/compare-{group['slug']}.png",
            "latest": {
                "reference_date": common_date.isoformat() if common_date else None,
                "values": latest_values,
            },
        })

    with open(output_path, "w") as f:
        json.dump({
            "generated_at": now_iso(),
            "groups": enriched,
        }, f, ensure_ascii=False, indent=2)
```

### Páginas Astro

#### `/comparar/index.astro`

```astro
---
import { readFileSync } from 'node:fs';
import path from 'node:path';
import BaseLayout from '../../layouts/BaseLayout.astro';

const { groups } = JSON.parse(
  readFileSync(path.resolve('./data/groups.json'), 'utf-8')
);

const meta = {
  title: 'Comparações entre indicadores | Indicadores Econômicos Hoje',
  description: 'Visualizações comparando os principais indicadores econômicos brasileiros lado a lado.',
};
---
<BaseLayout meta={meta}>
  <main>
    <h1>Comparações entre indicadores</h1>
    <p>Visualizações curadas dos principais indicadores brasileiros agrupados por tema.</p>

    <ul class="groups">
      {groups.map((g) => (
        <li>
          <a href={`/comparar/${g.slug}/`}>
            <img src={g.chart} alt={`Gráfico comparativo: ${g.title}`} loading="lazy" width="800" height="400" />
            <h2>{g.title}</h2>
            <p>{g.description}</p>
          </a>
        </li>
      ))}
    </ul>
  </main>
</BaseLayout>
```

#### `/comparar/[slug].astro`

```astro
---
import { readFileSync } from 'node:fs';
import path from 'node:path';
import BaseLayout from '../../layouts/BaseLayout.astro';

export async function getStaticPaths() {
  const { groups } = JSON.parse(
    readFileSync(path.resolve('./data/groups.json'), 'utf-8')
  );
  return groups.map((g) => ({
    params: { slug: g.slug },
    props: { group: g },
  }));
}

const { group } = Astro.props;
const meta = {
  title: `${group.title} | Indicadores Econômicos Hoje`,
  description: group.description,
};
---
<BaseLayout meta={meta}>
  <article>
    <h1>{group.title}</h1>
    <p>{group.description}</p>

    <img src={group.chart} alt={`Gráfico comparativo: ${group.title}`} width="1200" height="600" />

    <h2>Últimos valores (acumulado 12 meses)</h2>
    <table>
      <thead>
        <tr>
          <th>Indicador</th>
          <th>Valor mais recente</th>
          <th>Acumulado 12 meses</th>
        </tr>
      </thead>
      <tbody>
        {group.indicators.map((ind) => {
          const latest = group.latest.values[ind.code];
          return (
            <tr>
              <td><a href={`/${ind.slug}/`}>{ind.code} - {ind.name}</a></td>
              <td>{latest ? `${latest.value.toFixed(2)}%` : '—'}</td>
              <td>{latest && latest.last_12m != null ? `${latest.last_12m.toFixed(2)}%` : '—'}</td>
            </tr>
          );
        })}
      </tbody>
    </table>

    <h2>Indicadores incluídos</h2>
    <ul>
      {group.indicators.map((ind) => (
        <li><a href={`/${ind.slug}/`}>{ind.code} - {ind.name}</a></li>
      ))}
    </ul>
  </article>
</BaseLayout>
```

### Adicionar `/comparar/` ao header

A navegação principal ganha um item "Comparar" entre as categorias e o "Sobre".

### SEO

- Cada página `/comparar/{slug}/` tem `meta` próprio
- Imagem comparativa recebe `alt` descritivo
- Schema.org `Dataset` em cada `compare/{slug}/`:

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "{group.title}",
  "description": "{group.description}",
  "url": "https://indicadoreseconomicoshoje.com.br/comparar/{slug}/"
}
```

---

## Categoria nova: `/construcao-civil/`

A introdução do INCC-M cria a primeira página em `construcao_civil`. Replica o padrão das outras categorias:

```
/construcao-civil/
└── lista os indicadores da categoria (apenas INCC-M)
```

Texto introdutório curto:

> Indicadores ligados ao setor da construção civil no Brasil. Acompanham os custos de materiais, mão-de-obra e serviços usados em obras residenciais e comerciais.

---

## Performance e budgets

| Métrica | Budget |
|---|---|
| JS no cliente (gzipped) | < 5KB total |
| Tamanho HTML por página de detalhe | < 100KB (com tabela cheia) |
| LCP mobile | < 1s |
| CLS | 0 (PNGs com width/height fixos) |

> A tabela cheia escala mal para indicadores muito antigos (IGP-DI tem 990 linhas). Para esses, considerar paginação no servidor por ano (já fazemos via `<details>` por ano se necessário) — mas decidir só se o budget de HTML estourar.
