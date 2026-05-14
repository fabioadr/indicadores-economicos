# 04 — Charts Interativos, Sparklines e /comparar/

> Spec da modernização visual: substituir PNGs por gráficos interativos, com fallback funcional e budget de JS controlado.

## Visão geral

Três tipos de chart, com tecnologias diferentes:

| Tipo | Onde | Tecnologia | Por quê |
|---|---|---|---|
| **Sparkline** | Home (cards de indicador) | SVG inline server-side | Decorativo, estático, zero JS |
| **Detail chart** | Páginas `/{slug}/` | Chart.js client-side | Hover, zoom, mais dados |
| **Comparison chart** | `/comparar/` | Chart.js client-side multi-line | Toggle de séries |

Todos com **fallback noscript** apontando para PNG (gerado pelo matplotlib reduzido).

## Sparklines (M20)

### Visual

Pequena linha (~80x24 pixels) inline ao lado do valor atual em cada card da home, mostrando os últimos 12 meses do indicador. Sem eixos, sem labels — só a forma da curva.

Visualmente parecido com o sparkline do GitHub no histórico de contributions, mas linha em vez de barras.

### Geração

Em `pipeline/sparklines.py`:

```python
def build_sparkline_svg(
    values: list[float],
    width: int = 80,
    height: int = 24,
    stroke: str = 'currentColor',
    stroke_width: float = 1.5,
) -> str:
    """
    Gera SVG inline-ready (sem <?xml?>, sem namespace).
    Usa currentColor para herdar do tema (suporte a dark mode automático).
    Subsamples a >24 pontos para manter o SVG enxuto.
    """
    ...
```

Saída exemplo (formatada para leitura):

```html
<svg viewBox="0 0 80 24" width="80" height="24" aria-hidden="true">
  <polyline
    points="0,12 7,10 14,11 21,9 ... 80,4"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linejoin="round"
    stroke-linecap="round"
  />
</svg>
```

> Tamanho típico: ~600 bytes. 11 sparklines na home: ~7KB inline (sem requests adicionais).

### Componente Astro

```astro
---
// site/src/components/charts/Sparkline.astro
import sparklineData from '/public/data/sparklines.json';
const { slug } = Astro.props;
const svg = sparklineData[slug];
---
<div class="sparkline" set:html={svg} />
```

> O JSON `sparklines.json` é gerado pelo pipeline em build, com chave = slug e valor = string SVG. Gerado uma vez, lido N vezes pelo Astro.

### Fallback

Se um indicador não tiver sparkline (raro, só se dados insuficientes), exibir traço plano discreto. **Não** exibir loading nem placeholder visível.

## Detail chart (M21)

### Substituição do PNG

Hoje, página `/{slug}/` exibe um `<img src="/charts/{slug}.png">`. Passa a exibir um `<canvas>` com Chart.js.

### Setup de Chart.js (vendor minimal)

`site/src/components/charts/chartjs-setup.ts`:

```typescript
// Apenas o que é usado, para ficar dentro do budget
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Filler,
  Legend,
  Title,
} from 'chart.js';

Chart.register(
  LineController, LineElement, PointElement,
  LinearScale, CategoryScale, Tooltip, Filler, Legend, Title
);

// Defaults globais para visual consistente
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = 'currentColor';

export { Chart };
```

> **Não** importar `chart.js/auto` — traz ~70KB. O caminho acima fica em ~25KB gzipped.

### Componente DetailChart

`site/src/components/charts/DetailChart.astro`:

```astro
---
const { slug, name, unit } = Astro.props;
---
<div class="chart-container">
  <canvas data-chart-detail data-slug={slug} data-unit={unit}></canvas>
  <noscript>
    <img src={`/og/${slug}-fallback.png`} alt={`Gráfico ${name}`} />
    <p class="text-sm">
      Veja o histórico completo na <a href="#tabela">tabela abaixo</a>.
    </p>
  </noscript>
</div>

<script>
  import { Chart } from './chartjs-setup';
  
  document.querySelectorAll('[data-chart-detail]').forEach(async (canvas) => {
    const slug = canvas.dataset.slug;
    const data = await fetch(`/data/series-${slug}.json`).then(r => r.json());
    
    new Chart(canvas as HTMLCanvasElement, {
      type: 'line',
      data: {
        labels: Object.keys(data.values),
        datasets: [{
          label: data.name,
          data: Object.values(data.values),
          borderColor: 'currentColor',
          backgroundColor: 'rgba(0,0,0,0.05)',
          fill: true,
          tension: 0.2,
          pointRadius: 0,
          pointHoverRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.parsed.y.toFixed(2)}%`,
            },
          },
        },
        scales: {
          y: { ticks: { callback: (v) => `${v}%` } },
          x: { ticks: { maxTicksLimit: 12 } },
        },
      },
    });
  });
</script>
```

> Hidratação via `client:visible` do Astro. Chart só carrega quando entra no viewport.

### Filtros de período (já existentes na Fase 2)

Os filtros de período (12m, 24m, 5a, total) da Fase 2 continuam funcionando. Adaptação: ao filtrar a tabela, **também atualizar o range visível do chart** via `chart.options.scales.x.min/max` (sem refetch).

Adicionar na lógica de filtros existente (`site/src/lib/period-filter.ts`):

```typescript
function applyToChart(chartId: string, startPeriod: string, endPeriod: string) {
  const chart = window.__charts?.[chartId];
  if (!chart) return;
  chart.options.scales.x.min = startPeriod;
  chart.options.scales.x.max = endPeriod;
  chart.update('none');
}
```

> Registry `window.__charts` populado no construtor de cada chart (chartId = slug).

## Comparison chart (M22)

### Substituição dos PNGs combinatórios

Hoje, `/comparar/` lista PNGs gerados pelo pipeline. Passa a listar **cards interativos**, um por grupo curado, com Chart.js multi-linha.

### Configuração de grupos (mantém Fase 2)

`pipeline/config/indicator_groups.py` continua sendo a fonte de verdade dos grupos curados. Cada grupo tem:

- `slug`: identificador URL-friendly
- `title`: título exibido
- `description`: parágrafo curto
- `indicator_slugs`: lista de slugs do catálogo

Pipeline gera `comparisons.json` por grupo (em vez de PNG):

```json
{
  "inflacao-oficial": {
    "title": "Inflação oficial: IPCA vs INPC vs IGP-M",
    "description": "...",
    "labels": ["2020-01", "2020-02", ...],
    "datasets": [
      { "slug": "ipca", "name": "IPCA", "values": [0.21, 0.25, ...] },
      { "slug": "inpc", "name": "INPC", "values": [0.19, 0.17, ...] },
      { "slug": "igp-m", "name": "IGP-M", "values": [0.48, -0.04, ...] }
    ]
  },
  ...
}
```

### ComparisonChart component

`site/src/components/charts/ComparisonChart.astro`:

- Recebe `groupSlug`
- Renderiza `<canvas>` + legenda customizada com checkboxes (toggle de séries)
- Cores fixas por slug (mantém consistência entre grupos)
- Mesmo padrão de `client:visible`

### Tabela de cores por indicador

Definida em `site/src/components/charts/colors.ts`:

```typescript
export const INDICATOR_COLORS: Record<string, string> = {
  ipca:    '#1e40af',  // azul
  'ipca-15': '#3b82f6',
  'igp-m': '#dc2626',
  'igp-di': '#ea580c',
  inpc:    '#059669',
  'incc-m': '#7c3aed',
  'ipc-fipe': '#db2777',
  selic:   '#0891b2',
  cdi:     '#0284c7',
  tr:      '#475569',
  'pim-pf': '#ca8a04',
};
```

> Cores são determinísticas (mesmo indicador = mesma cor em todos os charts) e suficientemente distintas em contraste AA.

### Toggle de séries

Cada grupo renderiza uma legenda customizada abaixo do canvas:

```html
<ul class="legend">
  <li>
    <label>
      <input type="checkbox" data-toggle="ipca" checked>
      <span class="dot" style="background: #1e40af"></span>
      IPCA
    </label>
  </li>
  ...
</ul>
```

Handler atualiza `chart.data.datasets[i].hidden` e chama `chart.update()`.

## Performance

### Budget total por tipo de página

| Página | JS gzipped | Inclui | Limite |
|---|---|---|---|
| Home | ~3KB | filtros + sparklines (inline SVG) | 5KB |
| `/{slug}/` (detalhe) | ~30KB | Chart.js + lógica de filtros + JSON da série | 50KB |
| `/calculadora/{slug}/` | ~35KB | Chart.js (se houver) + calculadora + JSON | 50KB |
| `/comparar/` | ~30KB | Chart.js + lógica de toggle | 50KB |

> Chart.js é **shared chunk**: carregado uma vez por sessão, cache do browser cobre navegação interna.

### Estratégias de carregamento

- **Sparklines**: inline SVG, zero requests
- **Detail chart**: `client:visible` no canvas, fetch do JSON após entrar no viewport
- **Calculadora**: `client:visible`, fetch do `calc-{slug}.json` após entrar no viewport
- **Comparison chart**: `client:visible` por card

### Lighthouse alvos (mobile, 4G simulado)

- Performance: ≥ 90 (relaxado de 95 da Fase 2)
- Accessibility: ≥ 95
- Best Practices: ≥ 95
- SEO: ≥ 95

> Trade-off explícito: Performance cai de 95 para 90 por causa do Chart.js no LCP de páginas de detalhe. Aceito porque a feature ganha não justifica forçar 95.

## Validação automatizada

Em `scripts/validate-fase3-build.sh`:

```bash
#!/usr/bin/env bash
# Roda após build do Astro

set -euo pipefail

DIST="${SITE_DIR:-./site}/dist"

# 1. Sparklines geradas
echo "Validando sparklines..."
test -f "${DIST}/data/sparklines.json"

# 2. Bundle size
echo "Validando bundle size..."
TOTAL_JS=$(find "$DIST" -name '*.js' -exec gzip -c {} \; | wc -c)
LIMIT=$((50 * 1024 * 11))  # 50KB × 11 indicadores como teto bruto
if [ "$TOTAL_JS" -gt "$LIMIT" ]; then
  echo "FAIL: JS total gzipped ${TOTAL_JS} bytes > limite ${LIMIT}"
  exit 1
fi

# 3. Calc data
echo "Validando dados de calculadora..."
for slug in ipca ipca-15 igp-m igp-di inpc incc-m tr; do
  test -f "${DIST}/data/calc-${slug}.json"
done

# 4. OG images
echo "Validando OG images..."
for slug in ipca ipca-15 igp-m igp-di inpc incc-m tr selic cdi ipc-fipe pim-pf; do
  test -f "${DIST}/og/${slug}-og.png"
  test -f "${DIST}/og/${slug}-fallback.png"
done

# 5. Comparisons JSON
echo "Validando dados de comparações..."
test -f "${DIST}/data/comparisons.json"

echo "OK: build da Fase 3 passou nas validações."
```

## Acessibilidade dos charts

- `<canvas role="img" aria-label="Gráfico de evolução do IPCA, últimos 12 meses">`
- Tabela histórica (já existente) é descrita como **a fonte de verdade textual** dos dados; o chart é a representação visual
- Keyboard nav nos charts não é prioridade da Fase 3 (Chart.js tem suporte limitado nativo); aceito como gap conhecido — tabela cobre o caso de uso
- Toggle de séries no `/comparar/` é via `<input type="checkbox">` nativo (totalmente acessível)
