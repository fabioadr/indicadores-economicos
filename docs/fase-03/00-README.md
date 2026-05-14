# Documentação — Indicadores Econômicos Hoje · Fase 3

Conjunto de specs para a **Fase 3** do projeto. **Estes documentos pressupõem as Fases 1 e 2 implementadas e em produção.** Se algum item ainda estiver pendente, conclua antes (ver `docs/fase-02/07-implementation-plan.md`).

## Como ler

| # | Documento | Para quê |
|---|---|---|
| 01 | `01-vision-and-scope.md` | O que a Fase 3 entrega (e o que NÃO entrega) |
| 02 | `02-architecture-deltas.md` | O que muda na arquitetura vs. Fase 2 |
| 03 | `03-calculator.md` | Especificação da calculadora de correção monetária |
| 04 | `04-interactive-charts.md` | Chart.js nas páginas, sparklines na home, /comparar/ interativo |
| 05 | `05-indicators-catalog.md` | Catálogo: IPC-Fipe e PIM-PF Indústria Geral |
| 06 | `06-implementation-plan.md` | Sequência de milestones M17–M22 |
| 07 | `07-claude-code-setup-additions.md` | Adições ao setup do Claude Code |
| — | `CLAUDE-additions.md` | Trecho a anexar ao `CLAUDE.md` da raiz |

## Princípios herdados (não revisados)

- Static-first; SQLite local é a single source of truth
- Plugin pattern para conectores
- Idempotência em tudo
- Fail loud (Telegram para qualquer erro)
- Free tier de infra
- Versionamento de dados via git
- "JS mínimo no cliente, justificado por feature, sem framework" — *threshold revisado, não o princípio* (ver decisão 2)

## O que a Fase 3 introduz de novo

1. **Calculadora de correção monetária** — feature de produto mais ambiciosa do projeto até aqui, com 7 páginas dedicadas (uma por indicador) e SEO de cauda longa
2. **Chart.js nas páginas de detalhe** — substitui PNGs estáticos por gráficos interativos
3. **Sparklines na home** — pequeno marco visual sem custo de JS (SVG server-side)
4. **/comparar/ interativo** — multi-line Chart.js com toggle, substituindo os PNGs combinatórios da Fase 2
5. **2 indicadores mensais adicionais** — IPC-Fipe e PIM-PF Indústria Geral
6. **Budget de JS revisado** — de 5KB para ~50KB gzipped, justificado por substituir 600KB de PNGs por charts mais leves no agregado

## Como usar com Claude Code

1. Leia `00-README.md` da raiz (e revise os READMEs de fase-01 e fase-02 se for sua primeira sessão)
2. Para cada milestone do `06-implementation-plan.md`, abra uma sessão dedicada
3. Ao final de cada milestone, rode a skill `smoke-test-milestone` (atualizada para a Fase 3) e faça commit explícito
4. Use o subagent novo `chartjs-research` quando precisar consultar API/options do Chart.js sem poluir contexto principal
