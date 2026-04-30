# Documentação — Indicadores Econômicos Hoje

Conjunto de specs para implementação spec-driven do sistema. Lê na ordem:

| # | Documento | Para quê |
|---|---|---|
| 01 | `product-vision.md` | O que o produto é, para quem, e o que ele NÃO é |
| 02 | `architecture.md` | Visão arquitetural completa |
| 03 | `data-model.md` | Schema SQLite definitivo + migrações |
| 04 | `connectors.md` | Interface base + implementação BCB |
| 05 | `pipeline.md` | Scheduler, agregações, build/deploy |
| 06 | `site.md` | Estrutura Astro, IA, design system, SEO |
| 07 | `telegram-bot.md` | Comandos e notificações |
| 08 | `indicators-catalog.md` | Catálogo Fase 1: IPCA, CDI, TR |
| 09 | `implementation-plan.md` | Sequência de tarefas para o Claude Code |
| 10 | `claude-code-setup.md` | MCPs, skills, subagents e scripts a instalar |
| — | `CLAUDE.md` | Contexto persistente para Claude Code (vai no root do repo) |

**Como usar com Claude Code:**

1. Coloca todos os docs em `docs/` no repositório
2. Coloca o `CLAUDE.md` na raiz do repositório
3. Inicia o Claude Code na raiz e pede para ele ler `docs/00-README.md` antes de qualquer tarefa
4. Para cada milestone do `09-implementation-plan.md`, abre uma sessão dedicada com o escopo bem delimitado

**Convenções:**

- "Pipeline" = sistema local Python (coleta + build)
- "Site" = aplicação Astro estática deployada na Vercel
- "Bot" = Telegram bot embutido no pipeline
- Todo path absoluto neste documento usa o root do repositório como referência
