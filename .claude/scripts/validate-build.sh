#!/usr/bin/env bash
# Confere que o build gerou os artefatos esperados
set -e
ERRORS=0

check() {
  if [[ -e "$1" ]]; then
    echo "✓ $1"
  else
    echo "✗ FALTANDO: $1"
    ERRORS=$((ERRORS + 1))
  fi
}

check site/data/indicators.json
check site/data/ipca.json
check site/data/cdi.json
check site/data/tr.json
check site/public/charts/ipca-history.png
check site/public/charts/cdi-history.png
check site/public/charts/tr-history.png

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ $ERRORS arquivos faltando."
  exit 1
fi
echo "✓ Build válido."