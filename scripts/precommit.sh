#!/usr/bin/env bash
# Pre-commit / release smoke check: ruff + validate-build + pnpm check.
# Pytest fica fora deste wrapper porque pode ser longo — rode em paralelo via:
#   .venv/bin/pytest pipeline/ -q  (em outro terminal ou run_in_background)
#
# Exit code != 0 em qualquer falha. Output enxuto (só linhas com erro).
set -e

step() { echo; echo "=== $1 ==="; }

step "ruff check pipeline/"
RUFF=""
if command -v ruff >/dev/null 2>&1; then RUFF="ruff"; fi
if [[ -x .venv/bin/ruff ]]; then RUFF=".venv/bin/ruff"; fi
if [[ -z "$RUFF" ]]; then
  echo "⚠ ruff não instalado (skip). Instale com: .venv/bin/pip install ruff"
else
  $RUFF check pipeline/ || { echo "✗ ruff falhou"; exit 1; }
  echo "✓ ruff ok"
fi

step "validate-fase2-build.sh"
bash scripts/validate-fase2-build.sh

step "site astro check"
if (cd site && pnpm astro check >/tmp/astro-check.log 2>&1); then
  echo "✓ astro check ok"
else
  grep -E "error|Error|✘|✗" /tmp/astro-check.log | head -10
  echo "✗ astro check falhou (log: /tmp/astro-check.log)"
  exit 1
fi

echo
echo "✓ Pre-commit OK. Pytest separado: .venv/bin/pytest pipeline/ -q"
