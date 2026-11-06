# CLAUDE.md

@AGENTS.md

O `AGENTS.md` acima é a fonte única de instruções do projeto, válida para qualquer ferramenta.
Abaixo, só o que é específico do Claude Code.

## Python

Reforço da seção 1 do AGENTS.md: o interpretador é `.venv/bin/python`. Um hook (`.claude/hooks/bash_guard.py`)
bloqueia `python`, `python3`, `pip`, `pytest` e `ruff` chamados sem `.venv/bin/` e devolve o comando certo:
reexecute com a sugestão, sem investigar o ambiente. O SessionStart já informa se o venv está saudável.

## MCPs (`.mcp.json`)

- **sqlite**: use para consultar o banco (`list_tables`, `describe_table`, `read_query`) em vez de Bash.
  Alteração de dados ou schema continua sendo via migration (AGENTS.md seção 6); `write_query` só com pedido
  explícito. Se o MCP não conectar, use os fallbacks da seção 6 do AGENTS.md.
- **context7**: documentação atualizada de bibliotecas (Astro 7, Tailwind 4, python-telegram-bot, httpx etc.).

## Subagents (`.claude/agents/`)

| Agent | Quando usar |
|---|---|
| `bcb-research` | Mapear/validar `series_id` no BCB SGS |
| `sidra-research` | Mapear/validar `tabela`/`variavel`/`localidade` no IBGE SIDRA |
| `connector-smoke` | Rodar um conector real isolado antes de tocar no DB |
| `migration-author` | Gerar a migration de um indicador novo |
| `build-validator` | Build + validação de artefatos em background, devolve só PASS/FAIL |
| `log-triage` | Resumir falhas recentes de coleta/build |
| `docs-fetcher` | Buscar e resumir docs de uma biblioteca |

## Skills (`.claude/skills/`)

`add-indicator`, `add-comparison-group`, `debug-collection`, `release-check`, `smoke-test-milestone`
(são os runbooks da seção 11 do AGENTS.md).

## Hooks (`.claude/settings.json`)

- SessionStart: saúde do ambiente (disco montado, venv, bot, último cron) + resumo do DB.
- PreToolUse: venv obrigatório, confirmação antes de `git push`/`deploy`/`publish` (deploy na Vercel), confirmação para toda
  escrita via MCP do sqlite (alerta extra se destrutiva), lembrete do graphify em buscas.
- PostToolUse: orçamento de JS (~5KB gzipped) após `pnpm build`/`astro build`.
