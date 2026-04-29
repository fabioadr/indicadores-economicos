#!/usr/bin/env bash
# Atalhos para queries comuns sem precisar lembrar a sintaxe

DB="${DB_PATH:-./data/indicadores.db}"
case "${1:-}" in
  indicators) sqlite3 -header -column "$DB" "SELECT code, slug, frequency, active, last_collected_at FROM indicators;" ;;
  values)
    code="${2:?uso: inspect-db.sh values <CODE>}"
    sqlite3 -header -column "$DB" "
      SELECT reference_date, value, ytd, last_12m
      FROM indicator_values v JOIN indicators i ON v.indicator_id = i.id
      WHERE i.code = '$code' ORDER BY reference_date DESC LIMIT 24;
    " ;;
  errors)
    sqlite3 -header -column "$DB" "
      SELECT started_at, indicator_id, error_message
      FROM collection_logs WHERE status = 'error' ORDER BY started_at DESC LIMIT 10;
    " ;;
  builds)
    sqlite3 -header -column "$DB" "
      SELECT started_at, status, indicators_updated, git_commit_sha
      FROM build_logs ORDER BY started_at DESC LIMIT 10;
    " ;;
  *) echo "uso: inspect-db.sh {indicators|values <CODE>|errors|builds}" ;;
esac