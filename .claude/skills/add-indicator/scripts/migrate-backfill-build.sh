#!/usr/bin/env bash
set -euo pipefail

CODE="${1:-}"
if [[ -z "$CODE" ]]; then
  echo "Usage: $0 <INDICATOR_CODE>" >&2
  exit 1
fi

python -m pipeline.cli migrate
python -m pipeline.cli backfill "$CODE"
python -m pipeline.cli build
