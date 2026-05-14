# 06 — Plano de Implementação da Fase 3

> Sequência de milestones M17 a M22. Cada um é uma sessão dedicada do Claude Code.

## Princípios herdados

- Uma sessão por milestone, sempre
- `/clear` (ou nova sessão) entre milestones
- Não avançar se o smoke test não passar
- Commit explícito ao fim de cada milestone (`git commit -m "milestone N: <descrição>"`)
- Push após validar

## Sequência

```
M17 — Indicadores adicionais (IPC-Fipe + PIM-PF)
M18 — Calculadora: schema, dados e lógica
M19 — Calculadora: páginas e UI
M20 — Sparklines na home
M21 — Chart.js nas páginas de detalhe (substituir PNG)
M22 — /comparar/ interativo
```

Justificativa da ordem:
- M17 é o mais simples e valida que o pipeline da Fase 2 está saudável antes de mudar coisas
- M18 antes de M19 separa "produzir dados" de "consumir dados", facilita teste isolado
- M20 é uma evolução pequena que entrega valor visível imediatamente
- M21 é a maior mudança visual; vir depois de M20 dá tempo de Chart.js setup ser refinado
- M22 reusa tudo do M21 (Chart.js, padrão de hidratação)

---

## M17 — Indicadores adicionais

**Objetivo**: adicionar IPC-Fipe (BCB SGS) e PIM-PF (IBGE SIDRA) ao catálogo. Validar conector SIDRA com novo caso de uso.

**Pré-requisitos**:
- Subagent `bcb-research` confirma série 193 e parâmetros de IPC-Fipe
- Subagent `sidra-research` confirma tabela/variável/classificação de PIM-PF (Indústria Geral, sem ajuste sazonal)

**Entregas**:

- [ ] Migration `pipeline/db/migrations/003_calculator_flag.sql` adiciona coluna `calculator_enabled`
- [ ] Seed atualizando 7 indicadores existentes para `calculator_enabled = 1`
- [ ] Seed inserindo IPC-Fipe e PIM-PF (com `calculator_enabled = 0`)
- [ ] Categoria nova `atividade` com página `/atividade/`
- [ ] Backfill executado para ambos
- [ ] Site rebuildado e deployado

**Smoke test**:

```bash
# Validar migration aplicada
sqlite3 data/indicadores.db "PRAGMA table_info(indicators);" | grep calculator_enabled

# Validar flags corretas
sqlite3 data/indicadores.db "SELECT code, calculator_enabled FROM indicators ORDER BY code;"
# Esperado: 7 indicadores com 1, 4 com 0 (após M17: SELIC, CDI, IPCFIPE, PIMPFG)

# Backfill
python -m pipeline.cli backfill IPCFIPE
python -m pipeline.cli backfill PIMPFG

# Validar volume
sqlite3 data/indicadores.db \
  "SELECT code, COUNT(*) FROM indicator_values GROUP BY code ORDER BY code;"

# Build & deploy
python -m pipeline.cli build
python -m pipeline.cli publish

# Após deploy:
# - https://indicadoreseconomicoshoje.com.br/atividade/ existe
# - https://indicadoreseconomicoshoje.com.br/pim-pf/ existe
# - https://indicadoreseconomicoshoje.com.br/ipc-fipe/ existe
# - /status no bot Telegram lista 11 indicadores
```

**DoD M17**: 11 indicadores no ar, calculator_enabled correto em todos, categoria atividade existente.

---

## M18 — Calculadora: schema, dados e lógica

**Objetivo**: pipeline gera `calc-{slug}.json` para os 7 indicadores marcados; testes unitários da lógica de cálculo client-side.

**Pré-requisitos**: M17 concluído (calculator_enabled correto).

**Entregas**:

- [ ] `pipeline/calculator_data.py` — gera 1 JSON por indicador com `calculator_enabled = 1`
- [ ] `pipeline/builder.py` chama `calculator_data.build_all()` ao final do build
- [ ] Saída em `site/public/data/calc-{slug}.json` (versionado no git para auditabilidade)
- [ ] `pipeline/tests/test_calculator_data.py` valida 5 casos de referência
- [ ] `site/src/components/calculator/calculator-logic.ts` com função pura `calculateCorrection`
- [ ] `site/src/components/calculator/__tests__/calculator-logic.test.ts` (Vitest) com mesmos 5 casos
- [ ] `package.json` do site com Vitest configurado

**Casos de referência sugeridos** (validar com Calculadora do Cidadão BCB):

```
1. R$ 1.000,00 IPCA jan/2020 → dez/2024 → ~R$ 1.273,xx
2. R$ 1.000,00 IGP-M jan/2020 → dez/2024 → ~R$ 1.500,xx
3. R$ 1.000,00 INPC jan/2010 → jan/2020 → ~R$ 1.700,xx
4. R$ 5.000,00 IPCA jan/1995 → jan/2025 → ~R$ 30.000,xx (Plano Real era)
5. R$ 1.000,00 TR jan/2015 → dez/2020 → ~R$ 1.030,xx (TR muito baixa no período)
```

> Ajustar os valores esperados após confirmar com a fonte oficial. Tolerância: ±1% (arredondamentos diferem entre implementações).

**Smoke test**:

```bash
# Pipeline
python -m pipeline.cli build
ls site/public/data/calc-*.json | wc -l   # esperado: 7

# Tamanho razoável
du -sh site/public/data/calc-*.json
# esperado: cada arquivo entre 5KB e 50KB

# Testes
cd pipeline && pytest tests/test_calculator_data.py
cd site && npm run test
```

**DoD M18**: 7 JSONs gerados, testes passando dos dois lados (Python e TS), nenhuma página da calculadora ainda criada (vem no M19).

---

## M19 — Calculadora: páginas e UI

**Objetivo**: criar landing `/calculadora/` e páginas `/calculadora/{slug}/` para os 7 indicadores. UI funcional com fallback noscript.

**Pré-requisitos**: M18 concluído.

**Entregas**:

- [ ] `site/src/pages/calculadora/index.astro` — landing
- [ ] `site/src/pages/calculadora/[slug].astro` — getStaticPaths para os 7 slugs
- [ ] `site/src/components/calculator/Calculator.astro` — container
- [ ] `site/src/components/calculator/DateInput.astro` — selects mês + ano
- [ ] `site/src/components/calculator/ResultCard.astro` — card de resultado com `aria-live`
- [ ] `site/src/components/calculator/calculator-ui.ts` — bindings DOM, fetch lazy, query params
- [ ] OG image específica de calculadora (gerada pelo pipeline) por indicador
- [ ] Disclaimer + conteúdo educacional na página (texto seed do Claude Code; revisão humana posterior)
- [ ] Link para a calculadora em cada página de detalhe (`/{slug}/` → "Calcular correção pelo {NOME}")
- [ ] Link reverso da calculadora para a página de detalhe

**Smoke test**:

```bash
npm run build --prefix site
bash scripts/validate-fase3-build.sh

# No deploy:
# 1. /calculadora/ lista as 7 calculadoras
# 2. /calculadora/ipca/ funciona com cálculo conhecido (R$ 1.000 jan/2020 → dez/2024)
# 3. URL com query params (?valor=1000&inicio=2020-01&fim=2024-12) executa cálculo automaticamente
# 4. Compartilhamento gera URL correta no clipboard
# 5. JS desabilitado (DevTools): inputs visíveis, aviso correto, tabela histórica visível
# 6. Lighthouse mobile da página: SEO ≥ 95, Performance ≥ 90
# 7. Calculadora invocada via /calc IPCA 1000 2020-01 2024-12 no bot retorna mesmo valor
```

**DoD M19**: 7 calculadoras no ar, todas funcionando, validações passando, conteúdo seed em todas (não importa qualidade do texto — Fábio refina depois).

---

## M20 — Sparklines na home

**Objetivo**: cada card de indicador na home tem um sparkline SVG inline mostrando os últimos 12 meses.

**Pré-requisitos**: M17 concluído.

**Entregas**:

- [ ] `pipeline/sparklines.py` — função `build_sparkline_svg`
- [ ] `pipeline/builder.py` gera `site/src/data/sparklines.json` (mapping slug → string SVG) em build
- [ ] `site/src/components/charts/Sparkline.astro` — componente que lê do JSON e usa `set:html`
- [ ] Atualização do template do card da home para incluir o Sparkline
- [ ] CSS: sparkline usa `currentColor`; cor adapta a tema (light/dark)

**Smoke test**:

```bash
python -m pipeline.cli build

# Validar JSON
cat site/src/data/sparklines.json | jq 'keys | length'  # esperado: 11

# Validar SVG bem-formado
cat site/src/data/sparklines.json | jq -r '.ipca' | head -c 200

# Build do site
npm run build --prefix site

# No HTML estático
grep -c 'class="sparkline"' site/dist/index.html
# esperado: 11

# Dark mode: alternar tema na home, sparklines invertem cor
```

**DoD M20**: 11 sparklines visíveis na home, ~7KB total inline, sem requests adicionais, dark mode adapta.

---

## M21 — Chart.js nas páginas de detalhe

**Objetivo**: substituir os PNGs nas páginas `/{slug}/` por Chart.js interativo, mantendo fallback noscript.

**Pré-requisitos**: M20 concluído.

**Entregas**:

- [ ] `site/package.json` com `chart.js` instalado
- [ ] `site/src/components/charts/chartjs-setup.ts` com vendor minimal
- [ ] `site/src/components/charts/colors.ts` com cores fixas por slug
- [ ] `site/src/components/charts/DetailChart.astro` (component + script de hidratação)
- [ ] `pipeline/builder.py` atualizado: gera `series-{slug}.json` (formato compacto para chart) em build
- [ ] `pipeline/charts.py` refatorado: `generate_detail_chart` → `generate_fallback_chart` (PNG menor); `generate_og_image` mantido
- [ ] Páginas `/{slug}/` substituem `<img>` por `<DetailChart>`
- [ ] Adaptação dos filtros de período da Fase 2 para também atualizar o range do chart
- [ ] Hook PostToolUse de bundle size (Fase 2) com threshold ajustado para 50KB

**Smoke test**:

```bash
python -m pipeline.cli build
npm run build --prefix site
bash scripts/validate-fase3-build.sh

# Após deploy:
# 1. /ipca/ exibe chart interativo (canvas), hover mostra tooltip
# 2. JS desabilitado: <img> com fallback PNG aparece, link para tabela
# 3. Filtro 12m no topo da tabela atualiza o range visível do chart
# 4. Lighthouse Performance mobile ≥ 90 em /ipca/
# 5. Bundle JS gzipped da página de detalhe ≤ 50KB
# 6. Cores em hex declaradas em colors.ts conferem com chart renderizado
```

**DoD M21**: 11 páginas de detalhe com chart interativo, todas dentro do budget, fallback funciona com JS desabilitado, integração com filtros da Fase 2 OK.

---

## M22 — /comparar/ interativo

**Objetivo**: `/comparar/` substitui PNGs por Chart.js multi-line com toggle de séries, mantendo grupos curados.

**Pré-requisitos**: M21 concluído (Chart.js setup pronto).

**Entregas**:

- [ ] `pipeline/builder.py` deixa de gerar PNGs comparativos; passa a gerar `comparisons.json`
- [ ] `pipeline/charts.py`: função de comparação removida (ou mantida apenas para uso eventual via bot)
- [ ] `site/src/pages/comparar/index.astro` reformulada para listar cards
- [ ] `site/src/components/charts/ComparisonChart.astro` — multi-linha com legenda customizada
- [ ] Toggle de séries via checkbox (acessível, vanilla)
- [ ] Cores consistentes com `colors.ts` do M21

**Smoke test**:

```bash
python -m pipeline.cli build

# Validar JSON
test -f site/public/data/comparisons.json
cat site/public/data/comparisons.json | jq 'keys | length'   # esperado: ≥ 3 (grupos da Fase 2)

# PNGs comparativos não devem mais existir
test ! -d site/public/charts/comparisons || ls site/public/charts/comparisons | wc -l  # esperado: 0

npm run build --prefix site
bash scripts/validate-fase3-build.sh

# Após deploy:
# 1. /comparar/ exibe N cards (um por grupo)
# 2. Cada card tem chart multi-linha com cores consistentes com /comparar/ × páginas de detalhe
# 3. Checkbox de toggle funciona (clicar oculta/exibe a série)
# 4. JS desabilitado: cada card mostra os indicadores em texto + link para suas páginas de detalhe
```

**DoD M22**: `/comparar/` totalmente interativo, grupos da Fase 2 preservados, toggle funcional, sem PNGs comparativos no build.

---

## Definition of Done global da Fase 3

- [ ] 11 indicadores no ar (9 da Fase 2 + IPC-Fipe + PIM-PF)
- [ ] 7 calculadoras no ar (`/calculadora/{ipca,ipca-15,igp-m,igp-di,inpc,incc-m,tr}/`)
- [ ] Landing `/calculadora/` com lista
- [ ] Sparklines em todos os cards da home
- [ ] Chart.js nas 11 páginas de detalhe (com fallback noscript)
- [ ] `/comparar/` interativo (Chart.js + toggle), grupos curados preservados
- [ ] Categoria nova `/atividade/` no ar
- [ ] OG images dedicadas para todas as páginas (incluindo calculadoras)
- [ ] JS gzipped por página ≤ 50KB validado por script
- [ ] Lighthouse mobile: Performance ≥ 90, demais ≥ 95
- [ ] Bot Telegram com comandos `/calc` e `/grafico` operacionais
- [ ] 7 dias de operação sem incidentes graves após deploy
- [ ] README atualizado refletindo Fase 3

## Estimativa de esforço

| Milestone | Complexidade | Tempo de uma sessão de Claude Code |
|---|---|---|
| M17 | Baixa–Média | 2–3h |
| M18 | Média | 3–4h |
| M19 | Alta | 5–7h |
| M20 | Baixa | 1–2h |
| M21 | Média–Alta | 4–6h |
| M22 | Média | 3–4h |

Total estimado: 18–26 horas distribuídas em 6 sessões.

> Estimativa grossa. M19 é o maior risco (UI completa com a11y, fallback, integrações). Vale dividir M19 em duas sessões se ficar pesado: M19a (componentes + UI) e M19b (páginas + SEO + integrações).

## Backlog Fase 4 (registrado para referência)

Permanece em aberto após Fase 3:

- **Calculadora de investimento** (CDI/SELIC com IR, alíquotas regressivas, comparação CDB/Tesouro/poupança)
- **PIB** (frequência trimestral; exige schema/aggregations/render dedicados)
- **PNAD** (multi-dimensional; exige modelagem de séries relacionadas)
- **Comparação livre** entre indicadores (escolha pelo usuário em /comparar/)
- **Admin web local** (somente se demanda real surgir)
- **Conector FGV nativo** (somente se BCB falhar como espelho)
- **Migração IPCA→SIDRA** (somente se houver demanda regional)
- **Indicadores diários** (câmbio, bolsa) — fora de escopo permanente nas fases anteriores; reavaliar
