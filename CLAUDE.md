# CLAUDE.md

**Projeto**: Indicadores Econômicos Hoje — Astro+Tailwind estático + Python 3.12/SQLite local.
**Stack**: httpx, matplotlib, pytest, ruff. Sem ORM, sem Docker.
**Regras**: Static-first, idempotente, fail loud via Telegram. Plugin pattern.
**Antes de tasks complexas**: leia docs/00-README.md

## MCPs

**sqlite**: Não use execução bash, use o MCP SEMPRE para listar tabelas, queries, escritas etc, ou seja, para qualquer tarefa que seja possível ser feita por ele.
**context7**: Para consulta de documentação atualizada de bibliotecas e pacotes.

## Ambiente Python

Usar sempre: `.venv/bin/python`
Comando ativação: `source .venv/bin/activate`
NÃO procurar outros interpretadores.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
