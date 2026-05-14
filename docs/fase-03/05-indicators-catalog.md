# 05 — Catálogo de Indicadores da Fase 3

> 2 indicadores adicionais, ambos mensais (compatíveis com schema atual sem alterações).

## Resumo

| Code | Slug | Categoria | Conector | Calculator | Config |
|---|---|---|---|---|---|
| IPCFIPE | ipc-fipe | inflacao | bcb_sgs | 0 | series_id 193 |
| PIMPFG | pim-pf | atividade | ibge_sidra | 0 | tabela 8159, var 12606 (ver nota) |

> **Importante**: os IDs/tabelas devem ser **confirmados via subagents** (`bcb-research` para BCB; `sidra-research` para SIDRA) antes da implementação. Os valores acima são referência consolidada mas a fonte oficial sempre prevalece. **Não fazer seed sem validação.**

> Nota PIM-PF: a tabela 8159 ("Produção física industrial - Indicadores mensais e variações") é a referência principal, com séries variando por indústria e tipo de variação. Usar a variação **mensal** da **Indústria Geral** (sem ajuste sazonal). Subagent `sidra-research` deve confirmar variável e classificações exatas.

## IPC-Fipe

### Identidade

- **Nome completo**: Índice de Preços ao Consumidor da Fipe
- **Slug URL**: `ipc-fipe`
- **Categoria**: `inflacao` (já existente)
- **Frequência**: mensal (com 4 quadrissemanas + fechamento mensal)
- **Cobertura geográfica**: Município de São Paulo
- **Fonte primária**: FIPE (Fundação Instituto de Pesquisas Econômicas - USP)
- **Fonte usada**: BCB SGS, série 193 (espelho confiável da FIPE)
- **Início da série**: 1939-01 (uma das séries mais longas do Brasil)

### Por que adicionar

- Histórico extremamente longo (relevante para SEO de cauda longa: "IPC FIPE histórico", "inflação SP")
- Complementa a categoria de inflação com perspectiva regional (SP)
- Coleta trivial via BCB (mesmo padrão dos outros)
- Não exige calculadora própria (não é índice de correção monetária convencional)

### `calculator_enabled`: 0

Razão: IPC-Fipe é mais usado como termômetro econômico do que como índice de correção contratual. Adicionar calculadora dele exigiria explicações específicas (4 quadrissemanas vs. mensal) que confundiriam o leigo. Manter consistência: calculadoras apenas para indicadores cujo uso prático principal É correção (IPCA, IGP-M, etc.).

### Conteúdo da página

Texto descritivo deve incluir:
- O que é (índice de preços, base SP)
- Quem produz (FIPE/USP)
- Como difere do IPCA (cobertura, periodicidade de divulgação)
- Para que é usado (referência regional, análises econômicas)
- Disclaimer padrão

### SQL seed (template)

```sql
INSERT OR IGNORE INTO indicators (
  id, code, slug, name, description, long_description,
  category, unit, frequency, source_authority, source_url,
  connector, connector_config, first_period,
  active, calculator_enabled,
  page_title_template, meta_description_template
) VALUES (
  '<uuid-fixo-a-definir>',
  'IPCFIPE',
  'ipc-fipe',
  'IPC-Fipe - Índice de Preços ao Consumidor da Fipe',
  'Índice de inflação para o município de São Paulo, calculado pela FIPE/USP desde 1939. Uma das séries de preços mais longas do Brasil.',
  '## O que é o IPC-Fipe ...',
  'inflacao',
  'percent',
  'monthly',
  'FIPE - Fundação Instituto de Pesquisas Econômicas',
  'https://www.fipe.org.br/',
  'bcb_sgs',
  '{"series_id": 193}',
  '1939-01-01',
  1,
  0,
  'IPC-Fipe - Inflação SP atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
  'IPC-Fipe de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo desde 1939.'
);
```

## PIM-PF Indústria Geral

### Identidade

- **Nome completo**: Pesquisa Industrial Mensal - Produção Física - Indústria Geral
- **Slug URL**: `pim-pf`
- **Categoria**: `atividade` (**nova categoria**)
- **Frequência**: mensal
- **Cobertura geográfica**: Brasil
- **Fonte primária**: IBGE
- **Fonte usada**: IBGE SIDRA (subagent confirma tabela/variável exata)
- **Início da série**: ~2002-01 (PIM-PF reformulado)

### Por que adicionar

- Indicador-chave de atividade econômica (mostra se a indústria está produzindo mais ou menos)
- Inaugura a categoria `atividade` no site
- Valida o conector SIDRA com novo caso de uso (até agora só IPCA-15)
- Cumpre parte do backlog que prometia "Produção Industrial"

### `calculator_enabled`: 0

Razão: PIM-PF mede variação de produção física, não de preços. Não é índice de correção monetária. Calculadora não faz sentido conceitual.

### Granularidade

PIM-PF tem múltiplas dimensões: variação mensal, mensal com ajuste sazonal, interanual, acumulado no ano, acumulado 12m, por seções (extrativa, transformação, geral) e por subsetores. Para a Fase 3, **usar apenas**:

- **Variação mensal** da **Indústria Geral**, **sem ajuste sazonal**

Outras visões (com ajuste, por subsetor) ficam para fases futuras se houver demanda.

### Aggregations

PIM-PF é uma **variação percentual mensal**, igual aos outros indicadores. As mesmas agregações (acumulado 12m, YTD, etc.) se aplicam sem mudança de código.

### Conteúdo da página

Texto descritivo deve incluir:
- O que é (medida de produção física da indústria)
- Quem produz (IBGE)
- O que significa um valor positivo/negativo (mais ou menos produção do que no mês anterior)
- Para que é usado (acompanhamento de ciclo econômico)
- Sem ajuste sazonal: explicar brevemente
- Disclaimer padrão

### SQL seed (template)

```sql
INSERT OR IGNORE INTO indicators (
  id, code, slug, name, description, long_description,
  category, unit, frequency, source_authority, source_url,
  connector, connector_config, first_period,
  active, calculator_enabled,
  page_title_template, meta_description_template
) VALUES (
  '<uuid-fixo-a-definir>',
  'PIMPFG',
  'pim-pf',
  'PIM-PF - Produção Industrial (Indústria Geral)',
  'Variação mensal da produção física da indústria brasileira (Indústria Geral, sem ajuste sazonal), divulgada pelo IBGE.',
  '## O que é o PIM-PF ...',
  'atividade',
  'percent',
  'monthly',
  'IBGE - Instituto Brasileiro de Geografia e Estatística',
  'https://sidra.ibge.gov.br/',
  'ibge_sidra',
  '{"tabela": <CONFIRMAR>, "variavel": <CONFIRMAR>, "classificacoes": <CONFIRMAR>}',
  '2002-01-01',
  1,
  0,
  'PIM-PF - Produção Industrial atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
  'PIM-PF de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Variação mensal da produção industrial brasileira.'
);
```

## Categoria nova: `atividade`

URL: `/atividade/`. Apenas PIM-PF na Fase 3.

Página de categoria deve ter introdução breve sobre o que são "indicadores de atividade" (medem o ritmo da economia, não preços nem juros), abrindo espaço para PIB, PNAD, etc. em fases futuras.

## Atualização do `calculator_enabled` para indicadores existentes

A migration `003_calculator_flag.sql` adiciona a coluna com default `0`. Após migration, atualizar via seed/UPDATE:

```sql
UPDATE indicators SET calculator_enabled = 1 WHERE code IN (
  'IPCA', 'IPCA15', 'IGPM', 'IGPDI', 'INPC', 'INCCM', 'TR'
);
```

Verificação:
```sql
SELECT code, calculator_enabled FROM indicators ORDER BY code;
```

Esperado: 7 indicadores com `1`, demais com `0`.

## Smoke test pós-implantação

Após o setup do M17:

```bash
# Backfill
python -m pipeline.cli backfill IPCFIPE
python -m pipeline.cli backfill PIMPFG

# Build e validações
python -m pipeline.cli build
bash scripts/validate-fase3-build.sh
```

Validações esperadas:

1. SQLite tem ~1000 valores para IPC-Fipe (1939+ × 12 meses), ~280 para PIM-PF (~2002+)
2. JSONs gerados em `site/src/data/` para ambos
3. JSONs `calc-*.json` continuam aparecendo apenas para os 7 indicadores corretos
4. Página `/atividade/` lista PIM-PF
5. Página `/inflacao/` lista IPC-Fipe junto com os demais
6. `/ipc-fipe/` e `/pim-pf/` no ar com chart, tabela e texto
7. Bot Telegram, ao consultar `/status`, lista 11 indicadores ativos
