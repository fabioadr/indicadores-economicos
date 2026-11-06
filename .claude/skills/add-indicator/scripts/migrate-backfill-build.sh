#!/usr/bin/env bash
set -euo pipefail

CODE="${1:-}"
if [[ -z "$CODE" ]]; then
  echo "Usage: $0 <INDICATOR_CODE>" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT"
PY="$REPO_ROOT/.venv/bin/python"

"$PY" -m pipeline.cli migrate
"$PY" -m pipeline.cli backfill "$CODE"
"$PY" -m pipeline.cli build
