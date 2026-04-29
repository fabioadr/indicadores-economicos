# 06 — Site

## Framework

**Astro 4+** com TypeScript, Tailwind CSS e zero JS no cliente por padrão.

## Estrutura de URLs

```
/                          → Home com tabela consolidada
/inflacao/                 → Categoria
/juros/                    → Categoria
/correcao-monetaria/       → Categoria
/ipca/                     → Detalhe IPCA
/cdi/                      → Detalhe CDI
/tr/                       → Detalhe TR
/sobre/                    → Página estática
/politica-de-privacidade/  → Página estática
/contato/                  → Página estática (mailto)
/sitemap.xml               → Gerado pelo Astro
/robots.txt                → Estático
```

URLs sem `index.html`. Vercel resolve `/ipca/` automaticamente como `/ipca/index.html` interno.

## Arquitetura de Informação

### Home

1. **Hero**: título do site + 1 frase descritiva
2. **Tabela consolidada**: lista todos os indicadores com último valor, variação 12m, link para detalhe
3. **Por categoria**: 3 seções (Inflação, Juros, Correção) com cards rápidos
4. **Disclaimer**: card destacado com aviso de responsabilidade
5. **Rodapé**: links das páginas estáticas + contato

### Categoria

1. Título da categoria
2. Descrição curta (1 parágrafo) explicando o que é a categoria
3. Cards dos indicadores da categoria, com último valor e link

### Detalhe do indicador

Estrutura escaneável, do mais relevante ao menos:

1. **Header**: nome completo, código, ícone da categoria
2. **Card de destaque**: valor mais recente em fonte grande + data + variação 12m + YTD
3. **Gráfico do ano corrente** (PNG)
4. **Tabela do ano corrente**: meses do ano, valor mensal, YTD, 12m
5. **Tabela histórica**: navegação por ano (tabs ou select), todos os meses
6. **Gráfico histórico** (PNG)
7. **O que é**: descrição longa em prose
8. **Fonte**: link para a fonte oficial
9. **Disclaimer**: aviso de responsabilidade
10. **Indicadores relacionados**: outros da mesma categoria

## Design System

### Direção estética

**Editorial moderna, autoridade tranquila.** Não é dashboard de fintech, não é portal popular de notícia. Mais perto de FT (Financial Times) do que de InfoMoney.

### Paleta

```css
/* Tons fundamentais */
--bg: #fafaf7; /* off-white quente, papel */
--bg-elevated: #ffffff;
--ink: #1a1a1a; /* texto principal */
--ink-muted: #525252; /* secundário */
--ink-faint: #a3a3a3; /* terciário, captions */
--border: #e5e5e0; /* divisores sutis */

/* Categorias - cores semânticas discretas */
--cat-inflacao: #b91c1c; /* vermelho-tijolo */
--cat-juros: #1e3a8a; /* azul-marinho */
--cat-correcao-monetaria: #166534; /* verde-floresta */

/* Variação numérica */
--positive: #166534; /* alta (em inflação pode ser ruim, mas neutro visualmente) */
--negative: #b91c1c; /* baixa */
--neutral: #525252;
```

### Tipografia

```css
--font-display: "Fraunces", Georgia, serif; /* títulos, números de destaque */
--font-body: "Inter", -apple-system, sans-serif; /* corpo */
--font-mono: "JetBrains Mono", monospace; /* tabelas de números, código */
```

Fontes via Google Fonts ou self-hosted (preferível para performance — usar `@fontsource`).

### Componentes (`src/components/`)

```
ui/
├── Card.astro           # container base
├── DataTable.astro      # tabela responsiva mono em valores
├── Sparkline.astro      # mini-gráfico inline (Fase 1: span vazio; Fase 3: SVG)
├── ValueDisplay.astro   # número com sinal e unidade
├── CategoryPill.astro   # pílula colorida por categoria
└── Disclaimer.astro     # card de aviso

layout/
├── Header.astro
├── Footer.astro
├── Navigation.astro
└── BaseLayout.astro

domain/
├── IndicatorCard.astro       # card resumo (home/categoria)
├── IndicatorHero.astro       # destaque grande no detalhe
├── IndicatorTableYear.astro  # tabela do ano
├── IndicatorTableHistory.astro  # tabela histórica com navegação por ano
└── IndicatorChart.astro      # wrapper do PNG estático
```

### Layout

- Container max-width: `1100px`
- Espaçamento generoso entre seções (`py-16 md:py-24`)
- Mobile-first: todas as tabelas têm scroll horizontal em telas estreitas
- Sem sidebars — fluxo single-column

## SEO

### Meta tags por página

Geradas a partir dos JSONs:

```html
<title>{meta.title}</title>
<meta name="description" content="{meta.description}" />
<link rel="canonical" href="https://indicadoreseconomicoshoje.com.br{path}" />
<meta property="og:title" content="{meta.title}" />
<meta property="og:description" content="{meta.description}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="..." />
<meta name="twitter:card" content="summary" />
```

### Schema.org (JSON-LD)

Em cada página de detalhe de indicador, embutir:

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "IPCA - Índice de Preços ao Consumidor Amplo",
  "description": "...",
  "url": "https://indicadoreseconomicoshoje.com.br/ipca/",
  "creator": {
    "@type": "Organization",
    "name": "Banco Central do Brasil",
    "url": "https://www.bcb.gov.br/"
  },
  "temporalCoverage": "1980-01/..",
  "license": "https://creativecommons.org/licenses/by/4.0/"
}
```

### sitemap.xml e robots.txt

- `sitemap.xml` gerado pelo `@astrojs/sitemap`
- `robots.txt` permissivo:

```
User-agent: *
Allow: /
Sitemap: https://indicadoreseconomicoshoje.com.br/sitemap.xml
```

### Performance (Core Web Vitals)

- Sem fontes externas blocking (preload + font-display: swap)
- PNGs com `loading="lazy"` exceto o do destaque
- Sem JS no cliente na Fase 1
- HTML leve (< 50KB por página)
- LCP target: < 1s
- CLS: 0 (reservar espaço dos PNGs com `width`/`height`)

## Astro config

```javascript
// astro.config.mjs
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://indicadoreseconomicoshoje.com.br",
  output: "static",
  trailingSlash: "always",
  build: {
    format: "directory" // gera /ipca/index.html, URL final /ipca/
  },
  integrations: [tailwind(), sitemap()]
});
```

## Páginas dinâmicas

```astro
---
// src/pages/[slug].astro
import { readFileSync } from 'node:fs';
import path from 'node:path';

export async function getStaticPaths() {
  const index = JSON.parse(
    readFileSync(path.resolve('./data/indicators.json'), 'utf-8')
  );
  return index.indicators.map((ind) => ({
    params: { slug: ind.slug },
    props: { code: ind.code },
  }));
}

const { slug } = Astro.params;
const detail = JSON.parse(
  readFileSync(path.resolve(`./data/${slug}.json`), 'utf-8')
);
---
<BaseLayout meta={detail.meta}>
  <IndicatorHero indicator={detail} />
  <!-- ... -->
</BaseLayout>
```

## Vercel config (`vercel.json`)

```json
{
  "buildCommand": "cd site && pnpm build",
  "outputDirectory": "site/dist",
  "installCommand": "cd site && pnpm install",
  "framework": null,
  "redirects": [
    { "source": "/(.*)/index.html", "destination": "/$1/", "permanent": true }
  ]
}
```

## Acessibilidade

- HTML semântico (`<main>`, `<nav>`, `<article>`, `<table>`)
- Tabelas com `<caption>` e `<th scope="col">`
- Contraste mínimo AA (verificar com Lighthouse)
- Foco visível
- Sem armadilhas de teclado
- Imagens com `alt` descritivo (gráficos com resumo do que mostram)
