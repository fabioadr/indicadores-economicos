#!/usr/bin/env bash
# Instala entrada cron horária; o gatekeeping é feito por scheduled-collect via schedule_overrides.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CRON_LINE="0 * * * * cd $REPO && $REPO/.venv/bin/python -m pipeline.cli scheduled-collect >> $REPO/pipeline/logs/cron.log 2>&1"

TMPFILE=$(mktemp)
crontab -l 2>/dev/null | grep -Ev "pipeline\.cli (collect|scheduled-collect)" > "$TMPFILE" || true
echo "$CRON_LINE" >> "$TMPFILE"
crontab "$TMPFILE"
rm "$TMPFILE"
echo "✓ Cron instalado:"
crontab -l | grep "pipeline.cli"