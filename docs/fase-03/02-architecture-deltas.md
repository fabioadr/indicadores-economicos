# 02 — Deltas Arquiteturais da Fase 3

> Apenas o que **muda** ou é **adicionado** em relação à arquitetura entregue na Fase 2.
> Tudo o que não está aqui permanece como está.

## Visão de alto nível

```
ANTES (Fase 2):
  Pipeline → JSON + PNG (chart, OG, comparar/) → Astro build → Vercel
  Site: HTML + Astro Islands mínimos (filtros de período, vanilla TS)

DEPOIS (Fase 3):
  Pipeline → JSON (detalhe + compactJSON p/ calculadora + sparklineSVG) + PNG (apenas OG e fallback) → Astro build → Vercel
  Site: HTML + Astro Islands com Chart.js + Calculadora (vanilla TS)
```

## Mudanças no pipeline

### `pipeline/builder.py` — alterações

- Continua gerando JSON detalhado por indicador (consumido pelo Astro em build)
- **Novo**: gera `series-{slug}.json` em formato compacto, otimizado para download/parse no cliente. Usado pela calculadora e pelos charts interativos
- **Novo**: gera `sparkline-{slug}.svg` (string SVG inline-ready, ~600 bytes cada) para a home
- **Reduzido**: a função existente de geração de chart de detalhe agora gera apenas:
  - `{slug}-og.png` (1200x630, para Open Graph)
  - `{slug}-fallback.png` (responsivo, para `<noscript>`)
- Comparações: deixa de gerar PNGs combinatórios; passa a gerar `comparisons.json` com séries agregadas dos grupos curados

### `pipeline/sparklines.py` — novo módulo

- Função `build_sparkline_svg(values: list[float], width: int = 80, height: int = 24) -> str`
- Sem dependência de matplotlib (puro Python + string templating)
- Saída: SVG inline-ready, sem `<?xml?>`, sem `<style>`, com `currentColor` para herdar do tema
- Polyline com 12 ou 24 pontos máximo (subsampling se a série for maior)

### `pipeline/calculator_data.py` — novo módulo

- Para cada indicador "calculável" (campo `calculator_enabled` no DB), produz `calc-{slug}.json`:
  ```json
  {
    "slug": "ipca",
    "code": "IPCA",
    "name": "IPCA",
    "unit": "percent",
    "first_period": "1980-01",
    "last_period": "2026-04",
    "values": { "1980-01": 6.62, "1980-02": 4.62, ... }
  }
  ```
- Tamanho típico: ~30KB por indicador (45 anos × 12 meses × valor); gzip Vercel reduz a ~8KB
- Carregado on-demand pela calculadora (lazy); não vai em todas as páginas

### `pipeline/charts.py` — modificado

- Função `generate_detail_chart()` renomeada para `generate_fallback_chart()` (PNG menor, otimizado para `<noscript>`)
- Função `generate_og_image()` extraída como pública e separada (1200x630, com texto sobreposto: nome do indicador + último valor)
- Função `generate_comparison_chart()` removida (não há mais PNG comparativo)

### Schema do banco — adições mínimas

Nova coluna em `indicators`:

```sql
ALTER TABLE indicators ADD COLUMN calculator_enabled INTEGER NOT NULL DEFAULT 0;
```

- `1` = indicador suporta correção monetária (IPCA, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15, TR)
- `0` = não tem calculadora (SELIC, CDI, IPC-Fipe, PIM-PF)

> Diferença simples e clara: calculadora dedicada existe apenas para indicadores cujo cálculo natural é "corrigir um valor entre duas datas". CDI e SELIC fazem mais sentido como cálculo de investimento (Fase 4 candidata).

Migration: `pipeline/db/migrations/003_calculator_flag.sql`.

## Mudanças no site

### Estrutura de pastas — adições

```
site/
├── src/
│   ├── components/
│   │   ├── charts/                    # NOVO
│   │   │   ├── DetailChart.astro      # Wrapper com fallback noscript
│   │   │   ├── ComparisonChart.astro  # Multi-line com toggle
│   │   │   ├── Sparkline.astro        # Inline SVG (server-side)
│   │   │   └── chartjs-setup.ts       # Vendor import + config global
│   │   └── calculator/                # NOVO
│   │       ├── Calculator.astro       # Container
│   │       ├── calculator-logic.ts    # Pure compute functions
│   │       ├── calculator-ui.ts       # Bindings input → result
│   │       └── DateInput.astro        # Date picker mês/ano
│   └── pages/
│       └── calculadora/               # NOVO
│           ├── index.astro            # Landing
│           └── [slug].astro           # Página por indicador
└── public/
    ├── data/
    │   ├── calc-*.json                # NOVO (lazy-loaded)
    │   └── comparisons.json           # NOVO (substitui PNGs)
    └── og/                            # NOVO
        └── *.png                      # OG images por página
```

### Vendoring do Chart.js

- Não instalar via npm com tree-shaking — usar **import direto do build minimal** que cabe em ~25KB gzipped:
  ```ts
  // chartjs-setup.ts
  import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Tooltip,
    Filler,
    Legend
  } from 'chart.js';
  Chart.register(
    LineController, LineElement, PointElement,
    LinearScale, CategoryScale, Tooltip, Filler, Legend
  );
  export { Chart };
  ```
- Astro com `client:load` no componente que usa o chart
- Verificação de bundle size pós-build via `validate-fase3-build.sh`

### Lazy-loading da calculadora

- Calculadora usa `client:visible` em vez de `client:load`
- Dados (`calc-{slug}.json`) carregados via `fetch()` apenas quando o componente entra no viewport
- Em conexão lenta, exibe esqueleto + tabela histórica como fallback útil

### Fallback noscript em todas as páginas com Chart.js

```astro
<DetailChart slug={slug}>
  <noscript slot="fallback">
    <img src={`/og/${slug}-fallback.png`} alt={`Gráfico ${name}`} />
    <p>Veja o histórico completo na <a href="#tabela">tabela abaixo</a>.</p>
  </noscript>
</DetailChart>
```

## Mudanças no Telegram bot

Comandos novos (escopo pequeno, mais conveniência que necessidade):

- `/calc IPCA 1000 2020-01 2024-12` → calcula correção e responde com texto + imagem PNG do gráfico
- `/grafico IPCA 24m` → envia PNG do gráfico de 24 meses (gerado on-demand via matplotlib)

Esses comandos reusam a infraestrutura de matplotlib mantida na Fase 3.

## Coisas que NÃO mudam

- Schema (exceto a coluna `calculator_enabled`)
- Conectores existentes (BCB SGS, IBGE SIDRA)
- Pattern de plugins
- Bot Telegram (apenas comandos adicionais)
- Cron schedule (continua o mesmo)
- Deploy (continua git push → Vercel)
- Modelo de agendamento configurável da Fase 2
- Estrutura de categorias (apenas adiciona `atividade`)

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Chart.js cresce além do budget se features futuras forem adicionadas | Hook PostToolUse já existente da Fase 2 valida JS budget; threshold revisado para 50KB |
| Calculadora dá resultados divergentes de outros sites por arredondamento | Documentar fórmula exata na própria página (transparência); testes unitários com casos conhecidos |
| Páginas de calculadora poluem indexação se muitas variantes forem criadas | Manter exatamente 7 páginas + landing; sem URLs com query params indexáveis |
| matplotlib quebra ao só gerar OG/fallback (uso reduzido = uso menos testado) | Mantido nos smoke tests; CI manual valida ambas as imagens em cada milestone |
| Sparkline SVG quebra no Safari iOS (parsing diferente) | Testar manualmente em iOS antes do deploy do M20; usar atributos básicos (sem features SVG modernas) |
