# CLAUDE.md

**Projeto**: Indicadores Econômicos Hoje — Astro+Tailwind estático + Python 3.12/SQLite local.
**Stack**: httpx, matplotlib, pytest, ruff. Sem ORM, sem Docker.
**Regras**: Static-first, idempotente, fail loud via Telegram. Plugin pattern.
**Antes de tasks complexas**: leia docs/00-README.md

## MCPs

**sqlite**: Use para listar tabelas, queries e escritas
**context7**: Para consulta de documentação atualizada de bibliotecas e pacotes.

## Ambiente Python

Usar sempre: `.venv/bin/python`
Comando ativação: `source .venv/bin/activate`
NÃO procurar outros interpretadores.
