#!/usr/bin/env bash
# Instala entrada cron para o pipeline diário
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CRON_LINE="0 7 * * * cd $REPO && $REPO/.venv/bin/python -m pipeline.cli collect --all && $REPO/.venv/bin/python -m pipeline.cli publish >> $REPO/pipeline/logs/cron.log 2>&1"

TMPFILE=$(mktemp)
crontab -l 2>/dev/null | grep -v "pipeline.cli collect" > "$TMPFILE" || true
echo "$CRON_LINE" >> "$TMPFILE"
crontab "$TMPFILE"
rm "$TMPFILE"
echo "✓ Cron instalado:"
crontab -l | grep "pipeline.cli"