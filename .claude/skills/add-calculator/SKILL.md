---
name: add-calculator
description: Adiciona uma nova calculadora de correção monetária ao site. Use quando um indicador existente passa a suportar calculadora (set calculator_enabled = 1) e precisa de página dedicada gerada conforme o padrão da Fase 3.
---

# Skill: add-calculator

## Pré-condições

- Indicador já existe em `indicators` (ativo, com série coletada)
- Indicador é apropriado para correção monetária (índice de preço/correção mensal em %)

## Passos

### 1. Atualizar flag no DB

```sql
UPDATE indicators SET calculator_enabled = 1 WHERE code = '<CODE>';
```

### 2. Validar geração do JSON

```bash
python -m pipeline.cli build
test -f site/public/data/calc-<slug>.json
```

### 3. Página é gerada automaticamente

A rota `/calculadora/[slug].astro` usa `getStaticPaths` baseado em `calculator_enabled = 1`. Não precisa criar arquivo novo.

### 4. Adicionar caso de teste de referência

Em `pipeline/tests/test_calculator_data.py` e `site/.../calculator-logic.test.ts`:

- Adicionar 1 caso de cálculo conhecido (validar contra Calculadora do Cidadão BCB ou outra fonte oficial)

### 5. Adicionar conteúdo educacional seed

Em `site/src/data/calculator-content/<slug>.md` (criar se não existir):

- "Como é calculado"
- "Quando usar"
- "Fonte oficial"

> Conteúdo seed é draft — Fábio refina depois.

### 6. OG image

Pipeline gera automaticamente em `site/public/og/<slug>-calc-og.png`.

### 7. Validação

```bash
bash scripts/validate-fase3-build.sh
```

Checa que:
- `calc-<slug>.json` existe
- OG image dedicada existe
- Página `/calculadora/<slug>/` está no build

### 8. Smoke manual

Após deploy:
- Acessar `/calculadora/<slug>/`
- Executar cálculo do caso de teste
- Comparar resultado com fonte oficial (tolerância ±1%)