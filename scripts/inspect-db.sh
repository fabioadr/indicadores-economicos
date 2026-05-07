#!/usr/bin/env bash
# Atalhos para queries comuns sem precisar lembrar a sintaxe.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${DB_PATH:-$REPO_ROOT/data/indicadores.db}"
PY="$REPO_ROOT/.venv/bin/python"
case "${1:-}" in
  indicators)
    sqlite3 -header -column "$DB" "
      SELECT code, slug, frequency, active, last_collected_at FROM indicators;
    " ;;
  values)
    code="${2:?uso: inspect-db.sh values <CODE>}"
    sqlite3 -header -column "$DB" "
      SELECT reference_date, value, ytd, last_12m
      FROM indicator_values v JOIN indicators i ON v.indicator_id = i.id
      WHERE i.code = '$code' ORDER BY reference_date DESC LIMIT 24;
    " ;;
  errors)
    sqlite3 -header -column "$DB" "
      SELECT cl.started_at, i.code, cl.error_message
      FROM collection_logs cl LEFT JOIN indicators i ON cl.indicator_id = i.id
      WHERE cl.status = 'error' ORDER BY cl.started_at DESC LIMIT 10;
    " ;;
  builds)
    sqlite3 -header -column "$DB" "
      SELECT started_at, status, indicators_updated, git_commit_sha
      FROM build_logs ORDER BY started_at DESC LIMIT 10;
    " ;;
  schedule)
    sqlite3 -header -column "$DB" "
      SELECT cron_expression, enabled, last_run_at, next_run_at, description
      FROM schedule_overrides;
    " ;;
  status)
    DB_PATH="$DB" "$PY" - <<'PY'
import os, sqlite3
c = sqlite3.connect(os.environ["DB_PATH"])
def q(sql, *args):
    return c.execute(sql, args).fetchone()[0]
SQL_ERRORS = (
    "SELECT COUNT(*) FROM collection_logs "
    "WHERE status = 'error' "
    "AND started_at >= datetime('now', '-24 hours')"
)
print(f"indicators_active={q('SELECT COUNT(*) FROM indicators WHERE active = 1')}")
print(f"indicators_total={q('SELECT COUNT(*) FROM indicators')}")
print(f"last_collection={q('SELECT COALESCE(MAX(last_collected_at), ?) FROM indicators', 'none')}")
print(f"errors_24h={q(SQL_ERRORS)}")
row = c.execute("SELECT started_at, status FROM build_logs ORDER BY started_at DESC LIMIT 1").fetchone()
print(f"last_build={(row[0] + ' (' + row[1] + ')') if row else 'none'}")
PY
    ;;
  *)
    echo "uso: inspect-db.sh {indicators|values <CODE>|errors|builds|schedule|status}"
    ;;
esac
