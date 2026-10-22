#!/usr/bin/env bash
# Instala:
#   - cron horário: scheduled-collect (gatekeeping via schedule_overrides)
#   - cron semanal (segunda 08:00): gsc-collect && gsc-report
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$REPO/.venv/bin/python"
LOG="$REPO/pipeline/logs/cron.log"
COLLECT_LINE="0 * * * * cd $REPO && $PYTHON -m pipeline.cli scheduled-collect >> $LOG 2>&1"
GSC_LINE="0 8 * * 1 cd $REPO && $PYTHON -m pipeline.cli gsc-collect >> $LOG 2>&1 && $PYTHON -m pipeline.cli gsc-report >> $LOG 2>&1"

TMPFILE=$(mktemp)
crontab -l 2>/dev/null | grep -Ev "pipeline\.cli (collect|scheduled-collect|gsc-collect|gsc-report)" > "$TMPFILE" || true
echo "$COLLECT_LINE" >> "$TMPFILE"
echo "$GSC_LINE" >> "$TMPFILE"
crontab "$TMPFILE"
rm "$TMPFILE"
echo "✓ Cron instalado:"
crontab -l | grep "pipeline.cli"