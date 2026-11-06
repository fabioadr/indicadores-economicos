---
name: debug-collection
description: Investiga erro de coleta de indicador. Use quando uma execução de `pipeline collect`/`scheduled-collect` retornar erro, uma notificação Telegram de erro chegar, ou a coleta parar de acontecer.
---

# Debug de Coleta

Para volume de saída grande, prefira delegar aos subagents `log-triage` e `connector-smoke` em background — eles devolvem só sumário.

## Passos

0. **Ambiente primeiro** (falhas de ambiente não aparecem em `collection_logs`):
   - `mountpoint -q /mnt/wsl/dev` (disco do repo montado?)
   - `.venv/bin/python -c "import dotenv, httpx, telegram"` (venv saudável?)
   - `systemctl --user is-active indicadores-bot` e `journalctl --user -u indicadores-bot -n 30 --no-pager`
   - `schedule_overrides.last_run_at`: se parado há mais de 1 dia, o cron não está coletando. O
     `scheduled-collect` recupera o horário perdido na primeira hora cheia após o logon (`is_due` em
     `pipeline/core/cron.py`); parado mesmo assim indica cron/WSL/venv com problema.

1. **Identifique a falha** — invoque `log-triage` (idealmente em background) ou rode direto:
   - SQL de `scripts/debug/recent_collection_errors.sql` via SQLite MCP, ou
   - `bash scripts/inspect-db.sh errors` (exige o CLI `sqlite3`)

2. **Inspecione a configuração** do indicador afetado:
   - SQL de `scripts/debug/indicator_config.sql` (substitua o `code` no `WHERE`).

3. **Reproduza isoladamente** — invoque `connector-smoke` com o config, ou rode direto:

   - **BCB**: `.venv/bin/python scripts/debug/reproduce_bcb_fetch.py <series_id> [--since YYYY-MM-DD]`
   - **SIDRA**: `.venv/bin/python scripts/debug/reproduce_sidra_fetch.py <tabela> <variavel> --localidade '<loc>' [--since YYYY-MM-DD]`

4. **Categorize**:
   - HTTP 4xx → `series_id`/`tabela` inválido ou janela vazia
   - HTTP 5xx → fonte indisponível, retry mais tarde
   - JSONDecodeError → fonte devolveu HTML (manutenção)
   - ParseError → formato mudou na fonte
   - SIDRA "-" / "..." nas células → comportamento esperado, connector já trata
   - `ModuleNotFoundError` / processo nem inicia → ambiente (passo 0), não a fonte

5. **Recomende**:
   - Retry imediato (`.venv/bin/python -m pipeline.cli collect <CODE>`)
   - Aguardar e retry mais tarde
   - Atualizar `connector_config` (via migration nova, não UPDATE manual)
   - Reportar mudança de formato (issue + atualizar conector)
