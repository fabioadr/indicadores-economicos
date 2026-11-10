#!/usr/bin/env bash
set -euo pipefail

# Bootstrap completo do projeto numa máquina nova.
# Python é gerenciado pelo uv (não pelo sistema): upgrades do Ubuntu não quebram o .venv.
# Dependências estão em pyproject.toml; as versões exatas, em uv.lock.
PYTHON_VERSION="3.14"

command -v uv >/dev/null 2>&1 || {
  echo "✗ uv não encontrado. Instale: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
}

uv python install "$PYTHON_VERSION"
uv sync --managed-python

cd site
pnpm install
cd ..

mkdir -p data pipeline/logs site/data site/public/charts

cp -n pipeline/.env.example pipeline/.env || true
echo "✓ Setup completo. Edite pipeline/.env com suas credenciais."
