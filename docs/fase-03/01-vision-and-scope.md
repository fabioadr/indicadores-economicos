# 01 — Visão e Escopo da Fase 3

## Tema

**Experiência e Alcance.** A Fase 1 entregou o esqueleto. A Fase 2 ampliou o catálogo. A Fase 3 transforma o site de uma referência de consulta em uma **ferramenta** que o leigo usa para resolver um problema concreto (calcular correção monetária), e simultaneamente moderniza a apresentação dos dados (gráficos interativos, sparklines).

O ganho mais importante esperado é de **utilidade percebida e SEO de cauda longa**: cada calculadora vira uma página dedicada e otimizada para queries do tipo "simulador IPCA", "correção monetária IGP-M", "atualização TR poupança".

## O que a Fase 3 É

- Calculadora de correção monetária para 7 indicadores de inflação/correção (uma página dedicada por indicador + landing)
- Substituição dos gráficos PNG estáticos por Chart.js nas páginas de detalhe e em `/comparar/`
- Sparklines inline na home, geradas em build time como SVG (sem custo de JS)
- 2 indicadores mensais novos: IPC-Fipe (BCB SGS) e PIM-PF Indústria Geral (IBGE SIDRA)
- Revisão pública do budget de JS no cliente

## O que a Fase 3 NÃO é

| Não é | Por quê |
|---|---|
| Reescrita arquitetural | Pipeline e stack continuam os mesmos; mudanças são adições + uma substituição (PNG → Chart.js) |
| Calculadora de investimento (CDI/SELIC com IR) | Outra natureza (regras tributárias, comparações entre aplicações); merece feature dedicada — Fase 4 candidata |
| PIB | Frequência trimestral exige mudanças de schema, agregações e renderização. Justifica fase própria |
| PNAD | Estrutura multi-dimensional (taxa de desocupação, ocupados, etc.); tratamento dedicado |
| Admin web local | Bot Telegram cobre operação atual; não há demanda real |
| Conector FGV nativo | Decisão da Fase 2 mantida — usar BCB como espelho |
| Migração IPCA→SIDRA | Decisão da Fase 2 mantida — sem demanda por dados regionais |
| Login, comentários, newsletter, multi-linguagem | Fora de escopo permanente |
| Notificações de atualização para usuários | Não é parte do produto |

## Decisões explicitadas

### Decisão 1: calculadora como feature de cabeçalho

**Contexto**: o backlog listava "calculadora de rentabilidade" sem detalhar tipo, escopo ou apresentação.

**Decisão**: implementar **7 calculadoras de correção monetária** (IPCA, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15, TR) como **páginas dedicadas** com URL própria (`/calculadora/{slug}/`) mais uma landing `/calculadora/`. Não implementar calculadora de investimento (CDI/SELIC) nesta fase.

**Motivo**:
- Páginas dedicadas por indicador maximizam captura de tráfego de cauda longa (cada query "simulador X" tem sua página)
- Correção monetária é um cálculo simples e universalmente útil (aluguel, contratos, sentenças judiciais, etc.)
- Investimento exige tratamento de IR (alíquotas regressivas, isenções), liquidez, comparação com benchmarks — feature de outra natureza
- Permite validar o padrão antes de generalizar para outros tipos de calculadora

**Risco aceito**: páginas de calculadora exigem JS no cliente para serem úteis. Mitigado em decisão 2.

### Decisão 2: revisar budget de JS de 5KB para ~50KB gzipped

**Contexto**: a Fase 2 estabeleceu "JS mínimo no cliente, justificado por feature, sem framework", com budget de 5KB gzipped.

**Decisão**: manter o princípio (sem framework, vanilla TS/JS, justificado por feature) e revisar o **threshold** para **~50KB gzipped por página**. Composição esperada:

- Chart.js minimal build (apenas `Chart`, `LineController`, `LineElement`, `LinearScale`, `CategoryScale`, `Tooltip`, `Filler`): ~25KB gzipped
- Lógica de calculadora: ~5KB
- Componentes de UI (date pickers, formatters): ~5KB
- Margem para crescimento orgânico: ~15KB

**Motivo**:
- Páginas de detalhe atualmente carregam ~80KB de PNG por gráfico; Chart.js reusa o JS entre páginas (cacheable) e o JSON é menor que o PNG correspondente
- A calculadora não tem alternativa server-side viável (interação com inputs em tempo real)
- 50KB ainda é considerado leve pelos padrões web atuais e mantém Lighthouse mobile ≥ 90

**Não relaxado**:
- Sem framework no cliente — Chart.js é vendor-import direto, sem React/Vue/Svelte
- HTML deve continuar funcional sem JS (gráfico tem fallback noscript com link para PNG ou tabela)
- Calculadora SEM JS exibe a tabela histórica do indicador como fallback útil

### Decisão 3: sparklines via SVG server-side, não via Chart.js

**Contexto**: sparklines são pequenos gráficos inline na home, ao lado de cada card de indicador.

**Decisão**: gerar sparklines como **SVG inline no HTML em build time**. Sem JS, sem Chart.js para esse caso.

**Motivo**:
- Sparkline é decorativo e estático — interatividade não agrega
- Inline SVG renderiza junto com o HTML (zero round-trip, zero CLS)
- Cada sparkline pesa <1KB e o conjunto da home (9–11 cards) cabe em ~10KB
- Carregar Chart.js só para isso multiplicaria o JS da home por ~5x sem ganho

**Risco aceito**: ligeira duplicação de lógica (sparkline em SVG / chart de detalhe em Chart.js). Mitigado mantendo as duas implementações simples e isoladas.

### Decisão 4: substituir PNGs comparativos por /comparar/ interativo

**Contexto**: a Fase 2 entregou `/comparar/` com PNGs combinatórios pré-renderizados.

**Decisão**: substituir os PNGs comparativos por Chart.js interativo na própria página `/comparar/`. **Manter os grupos curados** (não abrir para escolha livre). Cada grupo vira um card com Chart.js multi-linha e toggle de séries.

**Motivo**:
- Mesma justificativa de mover detalhe para Chart.js — interatividade > imagem
- Grupos curados continuam sendo melhor UX para leigo do que escolha livre (paradoxo da escolha)
- Toggle de séries no chart já cobre 80% do que escolha livre permitiria
- O JSON consumido é o mesmo dos detalhes; reuso de cache do navegador

**Não escopo**: escolha livre de quais indicadores comparar. Fica para Fase 4 candidata se houver demanda.

### Decisão 5: defer PIB e PNAD com justificativa explícita

**Contexto**: backlog listava PIB e PNAD como indicadores adicionais.

**Decisão**: **não incluir** PIB nem PNAD na Fase 3.

**Motivo**:
- **PIB**: frequência trimestral. Schema atual modela período como `YYYY-MM` para indicadores mensais. Adicionar trimestral exige: novo valor `quarterly` no enum de frequência; nova lógica de agregação (não dá para calcular "12m" — usa "4 trimestres móveis"); rendering de chart e tabela diferentes (4 colunas/ano em vez de 12); template de SEO diferente. Significa schema, pipeline, site e seeds afetados — escopo de fase própria
- **PNAD**: além da frequência (mensal mas com taxa contínua trimestral), tem multi-dimensionalidade (taxa de desocupação, taxa de participação, ocupados, desocupados). Cada série precisa decisão de modelagem própria

**Risco aceito**: catálogo cresce menos do que o backlog originalmente sugeria. Compensado pelo ganho de produto (calculadora) ser maior.

### Decisão 6: matplotlib continua existindo, com escopo reduzido

**Contexto**: substituir PNGs por Chart.js poderia significar remover matplotlib do pipeline.

**Decisão**: **manter** matplotlib no pipeline, com escopo reduzido a:

- Geração de **OG images** (Open Graph) para compartilhamento social — `1200x630` PNG por indicador, gerado em build
- Fallback nas páginas de detalhe (`<noscript>` com `<img>` apontando para PNG)
- Geração eventual sob demanda via comando do bot Telegram (`/grafico IPCA` retorna PNG)

**Motivo**:
- OG images precisam ser PNGs (Twitter/Facebook não renderizam JS)
- Fallback noscript mantém o site funcional para crawlers e usuários sem JS
- Reaproveita código existente; remoção seria gratuita

**Consequência**: `pipeline/charts.py` permanece com função única (`generate_og_image()` + `generate_fallback_chart()`); função de chart de detalhe atual passa a ser apenas chamada pelos dois casos acima.

## Indicadores adicionados na Fase 3

| Code | Slug | Categoria | Fonte | Série/Tabela |
|---|---|---|---|---|
| IPCFIPE | ipc-fipe | inflacao | BCB SGS | 193 |
| PIMPFG | pim-pf | atividade | IBGE SIDRA | tabela 8159 (var. 12606), Indústria Geral |

> Os IDs/tabelas devem ser **confirmados** via subagents `bcb-research` (IPC-Fipe) e `sidra-research` (PIM-PF) antes de implementação. Valores acima são referência consolidada mas a fonte oficial sempre prevalece.

> Nova categoria: `atividade` (apenas PIM-PF na Fase 3). PIB e PNAD virão depois.

## Categorias após Fase 3

| Categoria (URL) | Indicadores |
|---|---|
| `/inflacao/` | IPCA, IPCA-15, IGP-M, IGP-DI, INPC, IPC-Fipe |
| `/juros/` | SELIC |
| `/correcao-monetaria/` | TR, CDI |
| `/construcao-civil/` | INCC-M |
| `/atividade/` | PIM-PF *(novo)* |

> Total: **11 indicadores** ao final da Fase 3.

## Métricas de sucesso

| Métrica | Alvo | Como medir |
|---|---|---|
| Calculadora funciona em todos os 7 indicadores | 100% | Smoke test do M19 |
| Lighthouse mobile (Performance) | ≥ 90 | Chrome DevTools, página de detalhe e calculadora |
| Lighthouse mobile (SEO/A11y/BP) | ≥ 95 | Chrome DevTools |
| JS gzipped por página | ≤ 50KB | `validate-fase3-build.sh` |
| Tempo de cálculo da calculadora | < 50ms perceived | Manual (sem flicker em mobile) |
| Cobertura de queries SEO de calculadora | 7 páginas indexadas | Search Console (pós-deploy) |

## Definition of Done global

- [ ] 7 páginas de calculadora no ar e funcionando
- [ ] Landing `/calculadora/` listando todas
- [ ] Páginas de detalhe com Chart.js (com fallback noscript)
- [ ] `/comparar/` com Chart.js interativo, mantendo grupos curados
- [ ] Sparklines em todos os cards da home
- [ ] IPC-Fipe e PIM-PF coletando, agregando, renderizando
- [ ] OG images geradas para todas as páginas (matplotlib reduzido)
- [ ] JS budget validado (≤ 50KB gzipped por página)
- [ ] Lighthouse mobile dentro dos alvos
- [ ] 7 dias de operação sem incidentes graves após deploy
- [ ] README atualizado refletindo Fase 3
