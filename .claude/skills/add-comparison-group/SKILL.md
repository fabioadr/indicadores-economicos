---
name: add-comparison-group
description: Adiciona um novo grupo de comparação à página /comparar/. Use quando o usuário pedir para criar uma nova visualização comparativa (ex: "compare IPCA, INPC e IGP-M num gráfico só").
---

# Adicionar Grupo de Comparação

Workflow para criar/editar grupos pré-renderizados em `pipeline/config_groups.py`.

## 1. Coletar requisitos

- **slug** (kebab-case, sem acentos): ex `juros-vs-inflacao`
- **title**: ex "Juros vs Inflação: SELIC e IPCA"
- **description** (1 frase): explicação para a página
- **indicators**: lista de codes (str) ou dicts `{code, metric, style}` para overrides
- **metric** default do grupo: `value`, `ytd`, `last_12m` (default), `last_24m`, `since_inception`

## 2. Validar pré-requisitos (sqlite MCP)

- Todos os codes existem em `indicators`?
  ```sql
  SELECT code FROM indicators WHERE code IN (...);
  ```
- Todos têm valores suficientes para a métrica? (`last_12m` requer 12+ pontos com valor não-nulo)
  ```sql
  SELECT i.code, COUNT(v.last_12m) AS n
  FROM indicators i LEFT JOIN indicator_values v ON v.indicator_id = i.id
  WHERE i.code IN (...) AND v.last_12m IS NOT NULL
  GROUP BY i.code;
  ```
- Faz sentido juntos? (comparar SELIC anualizada com IPCA mensal `value` distorce — preferir `last_12m`).

## 3. Editar `pipeline/config_groups.py`

Adicionar dict no array `INDICATOR_GROUPS`. Manter ordem (mais relevante primeiro).

## 4. Regenerar comparações

`bash scripts/regenerate-comparisons.sh`

(O script regenera só os PNGs comparativos e o `groups.json`; não toca em `data/<slug>.json` por indicador.)

## 5. Validar artefatos

- `site/public/charts/compare-<slug>.png` existe?
- `site/data/groups.json` contém entrada para o `slug`?
- `cd site && pnpm dev` → abrir `/comparar/<slug>/` e conferir render.

## 6. Commit

`git add pipeline/config_groups.py site/public/charts/compare-<slug>.png site/data/groups.json`

Mensagem: `site: add comparison group <slug>`.

## 7. Deploy (opcional)

`python -m pipeline.cli deploy` (se for ir para produção agora).

## Notas

- **Não** permitir comparações combinatórias livres — apenas grupos curados aqui.
- Se a métrica de um indicador específico precisa de override, use o formato dict (ver SELIC em `juros-vs-inflacao`).
- `style: "step"` é apropriado para indicadores que mudam em saltos discretos (ex: SELIC após reuniões do Copom).
