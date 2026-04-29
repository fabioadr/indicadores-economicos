#!/usr/bin/env bash
set -euo pipefail

# Bootstrap completo do projeto numa máquina nova
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r pipeline/requirements.txt

cd site
pnpm install
cd ..

mkdir -p data pipeline/logs site/data site/public/charts

cp -n pipeline/.env.example pipeline/.env || true
echo "✓ Setup completo. Edite pipeline/.env com suas credenciais."