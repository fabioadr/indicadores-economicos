#!/usr/bin/env bash
# Valida artefatos do build Fase 1 + Fase 2 (indicadores individuais e grupos).
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

# Fase 1
check site/data/indicators.json
for slug in ipca cdi tr; do
  check "site/data/${slug}.json"
  check "site/public/charts/${slug}-history.png"
done

# Fase 2: indicadores
for slug in selic igp-m igp-di inpc incc-m ipca-15; do
  check "site/data/${slug}.json"
  check "site/public/charts/${slug}-history.png"
done

# Fase 2: grupos
check site/data/groups.json
for slug in inflacao-oficial indices-fgv juros-vs-inflacao construcao-civil; do
  check "site/public/charts/compare-${slug}.png"
done

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ $ERRORS arquivos faltando."
  exit 1
fi
echo "✓ Build Fase 1 + Fase 2 válido."
