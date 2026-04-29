---
name: debug-collection
description: Investiga erro de coleta de indicador. Use quando uma execução de `pipeline collect` retornar erro ou notificação Telegram de erro chegar.
---

# Debug de Coleta

1. **Identifique a falha** — query em `.claude/skills/debug-collection/scripts/recent_collection_errors.sql` (use o SQLite MCP ou `sqlite3` com o arquivo SQL).

2. **Inspecione a configuração** — `.claude/skills/debug-collection/scripts/indicator_config.sql` (substitua o código do indicador no `WHERE`).

3. **Reproduza isoladamente** o erro sem o pipeline:

   `python .claude/skills/debug-collection/scripts/reproduce_bcb_fetch.py <series_id> [--since YYYY-MM-DD]`

   (Alternativa: REPL com `BCBSGSConnector().fetch({"series_id": ...}, since=...)` como antes.)

4. **Categorize o erro**:
   - HTTP 4xx → series_id inválido ou janela de datas vazia
   - HTTP 5xx → BCB indisponível, agendar retry
   - JSONDecodeError → BCB devolveu HTML (manutenção)
   - ParseError → formato de dado mudou na fonte

5. **Recomende a ação**:
   - Retry imediato
   - Aguardar e retry mais tarde
   - Atualizar config do indicador
   - Reportar mudança de formato (issue)
