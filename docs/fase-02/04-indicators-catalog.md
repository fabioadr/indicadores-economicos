# 04 — Catálogo de Indicadores Fase 2

> Este catálogo segue exatamente o mesmo formato do `08-indicators-catalog.md` da Fase 1. Use os mesmos padrões para `meta_title`/`meta_description` e estrutura de markdown.

> **IMPORTANTE**: cada `series_id` BCB e cada `tabela`/`variavel` SIDRA deve ser confirmado via subagent `bcb-research` antes da implementação. Os valores neste documento são referência sólida mas não substituem validação direta na fonte.

---

## SELIC

| Campo | Valor |
|---|---|
| `code` | `SELIC` |
| `slug` | `selic` |
| `name` | SELIC - Taxa Básica de Juros (acumulada no mês) |
| `category` | `juros` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil |
| `source_url` | https://www.bcb.gov.br/controleinflacao/historicotaxasjuros |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 4189}` |
| `inception_date` | `1986-06-01` |
| `expected_release_day` | 1 |

**Short description:** Taxa básica de juros da economia brasileira, definida pelo Copom (Comitê de Política Monetária). É a principal ferramenta do Banco Central para controlar a inflação.

**Long description (markdown):**

```markdown
## O que é a SELIC

A SELIC — Sistema Especial de Liquidação e de Custódia — é a taxa básica de juros da economia brasileira. É a referência usada pelo Banco Central como instrumento de política monetária para controlar a inflação.

## Tipos de SELIC

Existem duas formas comuns de se referir à SELIC:

- **Selic Meta**: a taxa-alvo definida pelo Copom (Comitê de Política Monetária) em suas reuniões periódicas, expressa em % ao ano.
- **Selic Efetiva**: a taxa média praticada de fato no mercado interbancário, ligeiramente abaixo da Meta. É a SELIC que aparece nesta página, acumulada no mês.

## Para que serve

- **Política monetária**: o Banco Central sobe a Selic para combater inflação e baixa para estimular a economia
- **Renda fixa**: títulos públicos como Tesouro Selic são remunerados pela taxa
- **Custo do crédito**: empréstimos, financiamentos e cartão de crédito têm custo influenciado pela Selic
- **Caderneta de poupança**: quando a Selic está acima de 8,5% a.a., a poupança rende 0,5% ao mês mais TR; abaixo disso, rende 70% da Selic mais TR

## Como é calculada

A versão mensal nesta página é a Selic efetiva acumulada nos dias úteis do mês. É divulgada no primeiro dia útil do mês seguinte.

## Fonte

Dados obtidos da série 4189 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
```

**SEO:**
- `meta_title`: `SELIC - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `SELIC mensal de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo da Selic desde 1986.`

---

## IGP-M

| Campo | Valor |
|---|---|
| `code` | `IGPM` |
| `slug` | `igp-m` |
| `name` | IGP-M - Índice Geral de Preços do Mercado |
| `category` | `inflacao` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil (espelhando FGV) |
| `source_url` | https://portalibre.fgv.br/ |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 189}` |
| `inception_date` | `1989-06-01` |
| `expected_release_day` | 30 |

**Short description:** Índice de inflação calculado pela FGV. Conhecido como "inflação do aluguel", é amplamente usado para reajuste de contratos, especialmente imobiliários.

**Long description (markdown):**

```markdown
## O que é o IGP-M

O IGP-M — Índice Geral de Preços do Mercado — é um indicador de inflação calculado e divulgado pela Fundação Getulio Vargas (FGV). É composto pela média ponderada de três outros índices:

- **IPA-M** (Índice de Preços por Atacado, peso 60%)
- **IPC-M** (Índice de Preços ao Consumidor, peso 30%)
- **INCC-M** (Índice Nacional do Custo da Construção, peso 10%)

## Como é calculado

A pesquisa ocorre entre o dia 21 do mês anterior e o dia 20 do mês de referência. O resultado costuma ser divulgado nos últimos dias do próprio mês de referência.

Por isso, o IGP-M tende a antecipar movimentos que o IPCA captura no mês seguinte — o IGP-M de um mês X reflete preços coletados antes do IPCA do mesmo mês X.

## Para que serve

- **Reajuste de aluguéis**: por décadas foi a referência padrão; ainda muito usado, ainda que muitos contratos tenham migrado para IPCA
- **Contratos privados**: planos de saúde, mensalidades, energia elétrica
- **Concessões e serviços públicos**: tarifas como pedágios e telecomunicações
- **Análise macroeconômica**: por incluir preços no atacado, é um termômetro mais sensível a choques de oferta

## IGP-M vs IPCA

- **IGP-M**: mais sensível a oscilações cambiais e preços de commodities (peso alto do atacado)
- **IPCA**: foca apenas no consumidor final, mais estável

Em períodos de desvalorização do real, o IGP-M sobe mais rápido que o IPCA.

## Fonte

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 189), que replica os valores oficiais publicados pela FGV.
```

**SEO:**
- `meta_title`: `IGP-M - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `IGP-M de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do IGP-M desde 1989.`

---

## IGP-DI

| Campo | Valor |
|---|---|
| `code` | `IGPDI` |
| `slug` | `igp-di` |
| `name` | IGP-DI - Índice Geral de Preços - Disponibilidade Interna |
| `category` | `inflacao` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil (espelhando FGV) |
| `source_url` | https://portalibre.fgv.br/ |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 190}` |
| `inception_date` | `1944-02-01` |
| `expected_release_day` | 10 |

**Short description:** Índice de inflação da FGV, similar ao IGP-M mas com período de coleta dentro do mês civil. Usado em contratos públicos e análise histórica de longo prazo.

**Long description (markdown):**

```markdown
## O que é o IGP-DI

O IGP-DI — Índice Geral de Preços - Disponibilidade Interna — é calculado pela FGV e é o "irmão mais velho" do IGP-M. Tem a mesma composição (IPA 60%, IPC 30%, INCC 10%), mas com janela de coleta diferente.

## Diferença para o IGP-M

- **IGP-DI**: coleta entre o dia 1 e o último dia do mês de referência (mês fechado)
- **IGP-M**: coleta entre o dia 21 do mês anterior e o dia 20 do mês de referência

Por isso o IGP-DI sai depois (entre os dias 5 e 10 do mês seguinte), enquanto o IGP-M é divulgado ainda no fim do mês de referência.

## Para que serve

- **Contratos públicos antigos**: muitos contratos de longa duração da União ainda referenciam o IGP-DI
- **Séries históricas longas**: o IGP-DI tem registros desde 1944, mais antigo que qualquer outro índice em uso ativo no Brasil
- **Análise econômica**: usado em estudos macroeconômicos por sua amplitude temporal

## Fonte

Espelho do Banco Central do Brasil (série SGS 190), replicando os valores oficiais publicados pela FGV.
```

**SEO:**
- `meta_title`: `IGP-DI - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `IGP-DI de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do IGP-DI desde 1944.`

---

## INPC

| Campo | Valor |
|---|---|
| `code` | `INPC` |
| `slug` | `inpc` |
| `name` | INPC - Índice Nacional de Preços ao Consumidor |
| `category` | `inflacao` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil (espelhando IBGE) |
| `source_url` | https://www.ibge.gov.br/explica/inflacao.php |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 188}` |
| `inception_date` | `1979-04-01` |
| `expected_release_day` | 10 |

**Short description:** Índice oficial de inflação para famílias de baixa renda, calculado pelo IBGE. É a referência principal para reajustes de salários e benefícios trabalhistas.

**Long description (markdown):**

```markdown
## O que é o INPC

O INPC — Índice Nacional de Preços ao Consumidor — é o irmão do IPCA, também calculado pelo IBGE. A diferença está no público-alvo:

- **IPCA**: famílias com renda de 1 a 40 salários mínimos
- **INPC**: famílias com renda de 1 a 5 salários mínimos

A cesta de consumo do INPC dá mais peso a alimentação, transporte público e habitação popular, refletindo o orçamento típico de famílias de menor renda.

## Para que serve

- **Reajuste salarial**: muitos acordos coletivos e dissídios usam o INPC como referência
- **Benefícios previdenciários e assistenciais**: o INSS reajusta benefícios pelo INPC
- **Pensão alimentícia**: comum a correção pelo INPC em decisões judiciais
- **Salário mínimo**: a política de valorização do salário mínimo geralmente usa o INPC

## Como é calculado

A pesquisa de preços ocorre durante o mês de referência em 11 áreas urbanas. O resultado é divulgado entre os dias 7 e 12 do mês seguinte, junto com o IPCA.

## INPC vs IPCA

Os dois índices andam próximos, mas o INPC costuma estar ligeiramente acima quando há aumentos significativos em alimentos básicos e transporte público.

## Fonte

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 188), que replica os valores oficiais publicados pelo IBGE.
```

**SEO:**
- `meta_title`: `INPC - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `INPC de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do INPC desde 1979.`

---

## INCC-M

| Campo | Valor |
|---|---|
| `code` | `INCCM` |
| `slug` | `incc-m` |
| `name` | INCC-M - Índice Nacional do Custo da Construção (Mercado) |
| `category` | `construcao_civil` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil (espelhando FGV) |
| `source_url` | https://portalibre.fgv.br/ |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 192}` |
| `inception_date` | `1989-06-01` |
| `expected_release_day` | 30 |

**Short description:** Índice da FGV que mede a evolução dos custos da construção civil habitacional no Brasil. Usado em contratos de financiamento imobiliário durante a fase de obra.

**Long description (markdown):**

```markdown
## O que é o INCC-M

O INCC-M — Índice Nacional do Custo da Construção, versão Mercado — é calculado pela FGV e mede a variação dos preços ligados à construção civil habitacional. Acompanha materiais de construção, serviços e mão-de-obra.

## Onde é usado

- **Financiamento imobiliário na planta**: contratos de imóveis em construção quase sempre são corrigidos pelo INCC-M até a entrega das chaves
- **Reajuste de obras**: aditivos contratuais em obras públicas e privadas
- **Construtoras**: planejamento de custos de obras em andamento

## Composição

Os preços coletados se dividem em:

- **Materiais e equipamentos**: cimento, aço, tijolos, telhas, vidros, esquadrias, etc.
- **Mão-de-obra**: pedreiros, eletricistas, encanadores, engenheiros
- **Serviços**: aluguel de equipamentos, transporte, projetos

A FGV pondera cada componente conforme o peso típico em uma obra residencial.

## Por que é diferente do IPCA

O INCC-M tende a divergir bastante do IPCA porque seu carrinho de compras é específico do setor de construção. Em períodos de aquecimento do mercado imobiliário, o INCC-M pode subir muito mais rápido que a inflação geral. Em períodos de retração, pode ficar bem abaixo.

## Fonte

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 192), que replica os valores oficiais publicados pela FGV.
```

**SEO:**
- `meta_title`: `INCC-M - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `INCC-M de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Custo da construção civil desde 1989.`

---

## IPCA-15

| Campo | Valor |
|---|---|
| `code` | `IPCA15` |
| `slug` | `ipca-15` |
| `name` | IPCA-15 - Índice de Preços ao Consumidor Amplo - 15 |
| `category` | `inflacao` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | IBGE |
| `source_url` | https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo-15.html |
| `connector_type` | `ibge_sidra` |
| `connector_config` | `{"tabela": 3065, "variavel": 355, "localidade": "N1[all]"}` |
| `inception_date` | `2000-05-01` |
| `expected_release_day` | 25 |

**Short description:** Prévia do IPCA, calculada pelo IBGE com janela de coleta antecipada. Sai antes do IPCA oficial e é usada como sinal antecipado da inflação do mês.

**Long description (markdown):**

```markdown
## O que é o IPCA-15

O IPCA-15 é uma versão antecipada do IPCA, calculada pelo IBGE com a mesma metodologia, mas com período de coleta diferente:

- **IPCA**: dia 1 ao último dia do mês (mês cheio)
- **IPCA-15**: dia 16 do mês anterior ao dia 15 do mês de referência

Como sai antes (em torno do dia 25 do mês de referência), o IPCA-15 funciona como uma prévia da inflação oficial. Os mercados financeiros acompanham de perto o IPCA-15 porque ajuda a antecipar o IPCA do mesmo mês.

## Para que serve

- **Antecipação de tendência**: economistas, investidores e o próprio Banco Central usam o IPCA-15 como sinal precoce
- **Política monetária**: o Copom acompanha o IPCA-15 entre suas reuniões para avaliar mudanças no cenário inflacionário
- **Mercado financeiro**: a divulgação do IPCA-15 frequentemente movimenta câmbio e juros futuros

## Diferença para o IPCA "cheio"

A diferença entre IPCA-15 e IPCA do mesmo mês costuma ser pequena (frações de ponto percentual), mas pode ser significativa em meses de choques de preços.

## Fonte

Dados obtidos da tabela 3065 do SIDRA/IBGE, variável 355 (variação mensal), agregado Brasil.
```

**SEO:**
- `meta_title`: `IPCA-15 - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `IPCA-15 de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Prévia oficial do IPCA, do IBGE.`

---

## SQL para seed

Arquivo: `pipeline/db/migrations/004_seed_phase2_indicators.sql`

```sql
-- Seeds Fase 2: SELIC, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15
-- IDs UUID v4 fixos para garantir idempotência

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description
) VALUES
(
    'd4e5f6a7-b8c9-4d0e-a1b2-3c4d5e6f7a8b',  -- gerar UUID v4 fixo aqui
    'SELIC',
    'selic',
    'SELIC - Taxa Básica de Juros (acumulada no mês)',
    'Taxa básica de juros da economia brasileira, definida pelo Copom (Comitê de Política Monetária). É a principal ferramenta do Banco Central para controlar a inflação.',
    '## O que é a SELIC ...',  -- expandir markdown completo
    'juros',
    'percent',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/controleinflacao/historicotaxasjuros',
    'bcb_sgs',
    '{"series_id": 4189}',
    '1986-06-01',
    1,
    1,
    'SELIC - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'SELIC mensal de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo da Selic desde 1986.'
),
(
    'e5f6a7b8-c9d0-4e1f-b2c3-4d5e6f7a8b9c',
    'IGPM',
    'igp-m',
    'IGP-M - Índice Geral de Preços do Mercado',
    '...',
    '...',
    'inflacao',
    'percent',
    'monthly',
    'Banco Central do Brasil (espelhando FGV)',
    'https://portalibre.fgv.br/',
    'bcb_sgs',
    '{"series_id": 189}',
    '1989-06-01',
    30,
    1,
    'IGP-M - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'IGP-M de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do IGP-M desde 1989.'
),
(
    'f6a7b8c9-d0e1-4f2a-c3d4-5e6f7a8b9c0d',
    'IGPDI',
    'igp-di',
    'IGP-DI - Índice Geral de Preços - Disponibilidade Interna',
    '...',
    '...',
    'inflacao',
    'percent',
    'monthly',
    'Banco Central do Brasil (espelhando FGV)',
    'https://portalibre.fgv.br/',
    'bcb_sgs',
    '{"series_id": 190}',
    '1944-02-01',
    10,
    1,
    'IGP-DI - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'IGP-DI de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do IGP-DI desde 1944.'
),
(
    'a7b8c9d0-e1f2-4a3b-d4e5-6f7a8b9c0d1e',
    'INPC',
    'inpc',
    'INPC - Índice Nacional de Preços ao Consumidor',
    '...',
    '...',
    'inflacao',
    'percent',
    'monthly',
    'Banco Central do Brasil (espelhando IBGE)',
    'https://www.ibge.gov.br/explica/inflacao.php',
    'bcb_sgs',
    '{"series_id": 188}',
    '1979-04-01',
    10,
    1,
    'INPC - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'INPC de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do INPC desde 1979.'
),
(
    'b8c9d0e1-f2a3-4b4c-e5f6-7a8b9c0d1e2f',
    'INCCM',
    'incc-m',
    'INCC-M - Índice Nacional do Custo da Construção (Mercado)',
    '...',
    '...',
    'construcao_civil',
    'percent',
    'monthly',
    'Banco Central do Brasil (espelhando FGV)',
    'https://portalibre.fgv.br/',
    'bcb_sgs',
    '{"series_id": 192}',
    '1989-06-01',
    30,
    1,
    'INCC-M - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'INCC-M de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Custo da construção civil desde 1989.'
),
(
    'c9d0e1f2-a3b4-4c5d-f6a7-8b9c0d1e2f3a',
    'IPCA15',
    'ipca-15',
    'IPCA-15 - Índice de Preços ao Consumidor Amplo - 15',
    '...',
    '...',
    'inflacao',
    'percent',
    'monthly',
    'IBGE',
    'https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo-15.html',
    'ibge_sidra',
    '{"tabela": 3065, "variavel": 355, "localidade": "N1[all]"}',
    '2000-05-01',
    25,
    1,
    'IPCA-15 - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'IPCA-15 de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Prévia oficial do IPCA, do IBGE.'
);
```

> Os UUIDs acima são placeholders ilustrativos. **Gerar UUIDs v4 reais** uma única vez antes de criar a migration e fixá-los na seed.

> Os textos longos completos devem ser expandidos no SQL real (escapando aspas com `''` no SQLite).

## Smoke test pós-implantação

```bash
python -m pipeline.cli backfill SELIC
python -m pipeline.cli backfill IGPM
python -m pipeline.cli backfill IGPDI
python -m pipeline.cli backfill INPC
python -m pipeline.cli backfill INCCM
python -m pipeline.cli backfill IPCA15
python -m pipeline.cli build
python -m pipeline.cli deploy
```

Validações esperadas:

| Indicador | Linhas esperadas no SQLite |
|---|---|
| SELIC | ~480 (40 anos × 12 meses) |
| IGPM | ~440 |
| IGPDI | ~990 (desde 1944) |
| INPC | ~565 |
| INCCM | ~440 |
| IPCA15 | ~310 (desde 2000) |

Validação visual: cada slug deve renderizar em produção (ex: `https://indicadoreseconomicoshoje.com.br/selic/`).
