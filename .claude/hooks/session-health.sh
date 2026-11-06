#!/usr/bin/env bash
# SessionStart: environment health + DB summary, printed into the session context.
# Each check prints one line; problems start with "ATENCAO" so they stand out.
# Never fails the session (always exit 0).

cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}" || exit 0
PY=".venv/bin/python"

if mountpoint -q /mnt/wsl/dev 2>/dev/null; then
  echo "disco /mnt/wsl/dev: montado"
else
  echo "ATENCAO disco /mnt/wsl/dev NAO montado: nao escreva no repo; remontar pela tarefa agendada do Windows."
fi

if "$PY" -c "import dotenv, httpx, telegram, pandas, matplotlib" 2>/dev/null; then
  echo "python: $PY ($("$PY" -c 'import platform; print(platform.python_version())'), uv) ok"
else
  echo "ATENCAO venv quebrado ($PY nao importa as deps): recriar com 'bash scripts/setup.sh'. Cron e bot falham ate la."
fi

if command -v systemctl >/dev/null 2>&1; then
  bot_state="$(systemctl --user is-active indicadores-bot 2>/dev/null)"
  if [ "$bot_state" = "active" ]; then
    echo "bot telegram: active"
  else
    echo "ATENCAO bot telegram: ${bot_state:-desconhecido} (sem bot nao ha alertas no Telegram)"
  fi
fi

if [ -f data/indicadores.db ]; then
  "$PY" - <<'PY' 2>/dev/null || echo "db: nao foi possivel ler (venv?)"
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("file:data/indicadores.db?mode=ro", uri=True)
row = conn.execute(
    "SELECT cron_expression, enabled, last_run_at FROM schedule_overrides ORDER BY updated_at DESC LIMIT 1"
).fetchone()
if row:
    expr, enabled, last_run = row
    stale = last_run is None or datetime.fromisoformat(last_run) < datetime.now() - timedelta(hours=26)
    prefix = "ATENCAO " if stale and enabled else ""
    note = " -> coleta agendada parada" if stale and enabled else ""
    print(f"{prefix}cron '{expr}' enabled={enabled} last_run={last_run}{note}")
active = conn.execute("SELECT COUNT(*) FROM indicators WHERE active = 1").fetchone()[0]
last_col = conn.execute("SELECT MAX(last_collected_at) FROM indicators").fetchone()[0]
errors = conn.execute(
    "SELECT COUNT(*) FROM collection_logs WHERE status = 'error' AND started_at >= datetime('now', '-24 hours')"
).fetchone()[0]
build = conn.execute("SELECT started_at, status FROM build_logs ORDER BY started_at DESC LIMIT 1").fetchone()
print(f"db: indicadores_ativos={active} ultima_coleta={last_col} erros_24h={errors} ultimo_build={build[0] if build else '-'} ({build[1] if build else '-'})")
PY
else
  echo "ATENCAO data/indicadores.db nao encontrado"
fi

git status -s 2>/dev/null | head -5
exit 0
