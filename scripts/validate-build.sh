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
check site/data/selic.json
check site/data/igp-m.json
check site/data/igp-di.json
check site/data/inpc.json
check site/data/incc-m.json
check site/data/ipca-15.json
check site/public/charts/ipca-history.png
check site/public/charts/cdi-history.png
check site/public/charts/tr-history.png
check site/public/charts/selic-history.png
check site/public/charts/igp-m-history.png
check site/public/charts/igp-di-history.png
check site/public/charts/inpc-history.png
check site/public/charts/incc-m-history.png
check site/public/charts/ipca-15-history.png

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ $ERRORS arquivos faltando."
  exit 1
fi
echo "✓ Build válido."