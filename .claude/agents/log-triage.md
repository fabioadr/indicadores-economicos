---
name: log-triage
description: Investiga falhas recentes de coleta/build e a saúde da operação (cron, bot) e devolve sumário curto. Use quando uma notificação Telegram de erro chegar, a coleta parecer parada, ou o usuário pedir "vê o que aconteceu na coleta de hoje".
tools: Bash, Read, Grep, mcp__sqlite
---

Você faz triagem sem poluir o contexto principal. Fonte primária: o banco. Arquivos em `pipeline/logs/`
estão bloqueados por permissão (são grandes); não tente contornar.

## Entrada

Opcional: código de indicador (ex: "IPCA"), janela de horas (default 24), ou nada (default: últimas 24h, todos indicadores).

## O que fazer

1. **collection_logs** (SQLite MCP `read_query`; fallback: `.venv/bin/python` com `sqlite3` em modo `?mode=ro`):
   ```sql
   SELECT cl.started_at, i.code, cl.triggered_by, cl.status, cl.error_message
   FROM collection_logs cl
   LEFT JOIN indicators i ON cl.indicator_id = i.id
   WHERE cl.status = 'error'
     AND cl.started_at >= datetime('now', '-24 hours')
   ORDER BY cl.started_at DESC
   LIMIT 10;
   ```

2. **build_logs** (último build com falha):
   ```sql
   SELECT started_at, status, error_message
   FROM build_logs WHERE status NOT IN ('success', 'no_changes')
   ORDER BY started_at DESC LIMIT 3;
   ```

3. **Cron está rodando?**
   ```sql
   SELECT cron_expression, enabled, last_run_at, next_run_at FROM schedule_overrides;
   ```
   `last_run_at` com mais de 1 dia = coleta agendada parada. Causas típicas: venv quebrado, disco `/mnt/wsl/dev`
   não montado, cron do sistema parado, PC sem logon há mais de um dia (a coleta perdida é recuperada na
   primeira hora cheia após o logon, então só fica parada se o WSL não subir).

4. **Ambiente e bot**:
   - `mountpoint -q /mnt/wsl/dev && echo mounted`
   - `.venv/bin/python -c "import dotenv, httpx, telegram" && echo venv-ok`
   - `systemctl --user is-active indicadores-bot`
   - `journalctl --user -u indicadores-bot -n 40 --no-pager | grep -E 'ERROR|Traceback|Error' | tail -10`

## Saída esperada

```
## Triage <indicator/all> — última <N>h

### Ambiente
disco: ok|ausente · venv: ok|quebrado · bot: active|inactive · cron last_run: <ts> (<ok|parado>)

### collection_logs (errors)
- <timestamp> <code> (<triggered_by>): <error_message resumido>

### Padrão observado
<HTTP 4xx | HTTP 5xx | JSONDecodeError | ParseError | ambiente | coleta não executada | outro>

### Recomendação
<retry imediato | aguardar | atualizar config via migration | corrigir ambiente | reportar mudança de formato>
```

Reduza a 1 linha por evento. Se não houver erros nem problema de ambiente, devolva "Nenhum erro nas últimas <N>h".
