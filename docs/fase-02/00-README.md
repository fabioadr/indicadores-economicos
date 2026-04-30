# Documentação — Indicadores Econômicos Hoje · Fase 2

Conjunto de specs para a **Fase 2** do projeto. **Estes documentos pressupõem a Fase 1 implementada e em produção.** Se a Fase 1 ainda não foi finalizada, conclua-a antes (ver `docs/09-implementation-plan.md` da Fase 1).

## Como ler

| # | Documento | Para quê |
|---|---|---|
| 01 | `01-vision-and-scope.md` | O que a Fase 2 entrega (e o que NÃO entrega) |
| 02 | `02-architecture-deltas.md` | O que muda na arquitetura vs. Fase 1 |
| 03 | `03-connectors.md` | Especificação do conector IBGE SIDRA |
| 04 | `04-indicators-catalog.md` | Catálogo: SELIC, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15 |
| 05 | `05-site-features.md` | Filtros de período (cliente) + comparação entre indicadores |
| 06 | `06-telegram-improvements.md` | Comandos de agendamento configurável |
| 07 | `07-implementation-plan.md` | Sequência de milestones M10–M16 |
| 08 | `08-claude-code-setup-additions.md` | Adições ao setup do Claude Code |
| — | `CLAUDE-additions.md` | Trecho a anexar ao `CLAUDE.md` da raiz |

## Princípios herdados da Fase 1 (não revisados)

- Static-first; SQLite local é a single source of truth
- Plugin pattern para conectores
- Idempotência em tudo
- Fail loud (Telegram para qualquer erro)
- Free tier de infra
- Versionamento de dados via git

## O que a Fase 2 introduz de novo

1. **Conector IBGE SIDRA** — primeira fonte além do BCB
2. **6 indicadores adicionais** — SELIC, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15
3. **JS mínimo no cliente** — Astro Islands para filtros de período (mudança de princípio explícita)
4. **Comparações pré-renderizadas** — PNGs combinatórios para grupos curados de indicadores
5. **Bot Telegram com agendamento configurável** — controle de cron via comandos

## Como usar com Claude Code

1. Leia `00-README.md` da Fase 1 primeiro, depois este
2. Para cada milestone do `07-implementation-plan.md`, abra uma sessão dedicada
3. Anexe o conteúdo de `CLAUDE-additions.md` no `CLAUDE.md` da raiz do repo antes de iniciar a Fase 2

## Pré-requisitos para começar

- [ ] Fase 1 com Definition of Done global concluída
- [ ] Site no ar com IPCA, CDI e TR funcionando
- [ ] Cron diário rodando há pelo menos uma semana sem incidente
- [ ] Bot Telegram operacional e respondendo
- [ ] Backup recente do `data/indicadores.db`

## Convenções (recap)

- "Pipeline" = sistema local Python (coleta + build)
- "Site" = Astro estática deployada na Vercel
- "Bot" = Telegram bot
- "Fase 1" = MVP descrito em `docs/` da raiz
- "Fase 2" = este pacote de docs
- Todos os paths relativos usam o root do repositório como referência
