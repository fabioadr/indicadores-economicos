---
name: debug-collection
description: Investiga erro de coleta de indicador. Use quando uma execução de `pipeline collect` retornar erro ou notificação Telegram de erro chegar.
---

# Debug de Coleta

Para volume de saída grande, prefira delegar aos subagents `log-triage` e `connector-smoke` em background — eles devolvem só sumário.

## Passos

1. **Identifique a falha** — invoque `log-triage` (idealmente em background) ou rode direto:
   - SQL: `.claude/skills/debug-collection/scripts/recent_collection_errors.sql` via SQLite MCP, ou
   - `bash scripts/inspect-db.sh errors`

2. **Inspecione a configuração** do indicador afetado:
   - SQL: `.claude/skills/debug-collection/scripts/indicator_config.sql` (substitua o `code` no `WHERE`).

3. **Reproduza isoladamente** — invoque `connector-smoke` com o config, ou rode direto:

   - **BCB**: `python .claude/skills/debug-collection/scripts/reproduce_bcb_fetch.py <series_id> [--since YYYY-MM-DD]`
   - **SIDRA**: `python .claude/skills/debug-collection/scripts/reproduce_sidra_fetch.py <tabela> <variavel> --localidade '<loc>' [--since YYYY-MM-DD]`

4. **Categorize**:
   - HTTP 4xx → `series_id`/`tabela` inválido ou janela vazia
   - HTTP 5xx → fonte indisponível, retry mais tarde
   - JSONDecodeError → fonte devolveu HTML (manutenção)
   - ParseError → formato mudou na fonte
   - SIDRA "-" / "..." nas células → comportamento esperado, connector já trata

5. **Recomende**:
   - Retry imediato (`python -m pipeline.cli collect <CODE>`)
   - Aguardar e retry mais tarde
   - Atualizar `connector_config` (UPDATE em `indicators`)
   - Reportar mudança de formato (issue + atualizar conector)
