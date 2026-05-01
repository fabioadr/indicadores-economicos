# 08 — Catálogo de Indicadores Fase 1

## IPCA

| Campo | Valor |
|---|---|
| `code` | `IPCA` |
| `slug` | `ipca` |
| `name` | IPCA - Índice Nacional de Preços ao Consumidor Amplo |
| `category` | `inflacao` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil |
| `source_url` | https://www.bcb.gov.br/estatisticas/indecoreestrut |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 433}` |
| `inception_date` | `1980-01-01` |
| `expected_release_day` | 10 |

**Short description:** Indicador oficial de inflação do Brasil. Calculado pelo IBGE, mede a variação dos preços de produtos e serviços para famílias com renda entre 1 e 40 salários mínimos.

**Long description (markdown):**

```markdown
## O que é o IPCA

O IPCA — Índice Nacional de Preços ao Consumidor Amplo — é o indicador oficial de inflação do Brasil. É calculado e divulgado mensalmente pelo IBGE (Instituto Brasileiro de Geografia e Estatística).

## Como é calculado

O IPCA mede a variação de preços de uma cesta de produtos e serviços consumidos por famílias com renda entre 1 e 40 salários mínimos, em 13 áreas urbanas (regiões metropolitanas, Brasília e Goiânia).

A pesquisa de preços ocorre durante todo o mês de referência. O resultado é divulgado entre os dias 7 e 12 do mês seguinte.

## Para que serve

- **Meta de inflação**: o Banco Central usa o IPCA como referência para sua política monetária e meta oficial de inflação.
- **Reajustes**: muitos contratos, salários e benefícios são corrigidos pelo IPCA.
- **Análises econômicas**: é a referência mais usada para discutir inflação no Brasil.

## Fonte

Os dados desta página são obtidos da API do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil, série 433.
```

**SEO:**

- `meta_title`: `IPCA - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `IPCA de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Tabela histórica completa desde 1980.`

---

## CDI

| Campo | Valor |
|---|---|
| `code` | `CDI` |
| `slug` | `cdi` |
| `name` | CDI - Certificado de Depósito Interbancário |
| `category` | `juros` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil |
| `source_url` | https://www.bcb.gov.br/ |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 4391}` |
| `inception_date` | `1986-08-01` |
| `expected_release_day` | 1 |

**Short description:** Taxa de juros média dos empréstimos entre bancos. Referência principal para investimentos de renda fixa e cálculo de rentabilidade no Brasil.

**Long description (markdown):**

```markdown
## O que é o CDI

O CDI — Certificado de Depósito Interbancário — é a taxa média de juros das operações de empréstimo de um dia entre os bancos. Esse mercado existe porque, ao final de cada dia, alguns bancos têm sobra e outros têm falta de caixa, e fazem operações de curtíssimo prazo entre si.

## Como funciona

A taxa CDI acompanha de perto a Selic, a taxa básica de juros definida pelo Banco Central. Em geral, o CDI fica ligeiramente abaixo da Selic.

A versão mensal acumula as taxas diárias do mês. É divulgada no primeiro dia útil do mês seguinte.

## Para que serve

- **Benchmark de renda fixa**: muitos investimentos (CDBs, fundos DI, LCIs, LCAs) são remunerados como percentual do CDI (ex: "120% do CDI").
- **Custo de operações**: empréstimos e financiamentos entre bancos têm o CDI como referência.
- **Comparação de aplicações**: ao comparar duas aplicações de renda fixa, o CDI é a régua mais usada.

## Fonte

Dados obtidos da série 4391 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
```

**SEO:**

- `meta_title`: `CDI - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `CDI mensal de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do CDI desde 1986.`

---

## TR

| Campo | Valor |
|---|---|
| `code` | `TR` |
| `slug` | `tr` |
| `name` | TR - Taxa Referencial |
| `category` | `correcao_monetaria` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil |
| `source_url` | https://www.bcb.gov.br/ |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 226}` |
| `inception_date` | `1991-03-01` |
| `expected_release_day` | 1 |

**Short description:** Taxa usada para correção monetária da poupança, FGTS e financiamentos imobiliários no Brasil. Calculada e divulgada diariamente pelo Banco Central.

**Long description (markdown):**

```markdown
## O que é a TR

A TR — Taxa Referencial — é um índice de correção monetária criado em 1991. Foi originalmente desenhada para servir de referência para juros no Brasil em um período de inflação alta.

## Onde é usada

Atualmente a TR é aplicada principalmente em:

- **Caderneta de poupança**: o rendimento é a TR somada a 0,5% ao mês (ou 70% da Selic, dependendo do nível da Selic).
- **FGTS**: o saldo é corrigido pela TR somada a 3% ao ano.
- **Financiamentos imobiliários**: especialmente os do Sistema Financeiro de Habitação (SFH), usam a TR para corrigir o saldo devedor.

## Como é calculada

A TR é derivada da Taxa Básica Financeira (TBF), que reflete a média de juros pagos pelos bancos em CDBs prefixados de 30 dias. Sobre a TBF aplica-se um redutor para chegar à TR.

A versão mensal corresponde à TR vigente do primeiro dia do mês.

## Fonte

Dados obtidos da série 226 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
```

**SEO:**

- `meta_title`: `TR - Taxa Referencial - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `TR de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico da Taxa Referencial desde 1991.`

---

## SELIC

| Campo | Valor |
|---|---|
| `code` | `SELIC` |
| `slug` | `selic` |
| `name` | SELIC - Taxa Básica de Juros (anualizada) |
| `category` | `juros` |
| `unit` | `percent` |
| `frequency` | `monthly` |
| `source_name` | Banco Central do Brasil |
| `source_url` | https://www.bcb.gov.br/controleinflacao/historicotaxasjuros |
| `connector_type` | `bcb_sgs` |
| `connector_config` | `{"series_id": 4189}` |
| `inception_date` | `1986-06-01` |
| `expected_release_day` | 1 |

> **Observação:** a série SGS 4189 retorna a Selic **anualizada base 252 (% a.a.)**, não variação mensal. Os demais indicadores deste site são em % a.m. — manter atenção em comparações e em cálculos derivados (`last_12m`, comparações multi-indicador).

**Short description:** Taxa básica de juros da economia brasileira, definida pelo Copom. Expressa em % ao ano (anualizada base 252) e revista a cada reunião do Copom, aproximadamente a cada 45 dias.

**Long description (markdown):**

```markdown
## O que é a SELIC

A SELIC — Sistema Especial de Liquidação e de Custódia — é a taxa básica de juros da economia brasileira. É a referência usada pelo Banco Central como instrumento de política monetária para controlar a inflação.

## Tipos de SELIC

Existem duas formas comuns de se referir à SELIC:

- **Selic Meta**: a taxa-alvo definida pelo Copom (Comitê de Política Monetária) em suas reuniões periódicas, expressa em % ao ano.
- **Selic Efetiva**: a taxa média praticada de fato no mercado interbancário, ligeiramente abaixo da Meta. É a SELIC apresentada nesta página.

## Como é expressa

Diferente do CDI mensal, do IPCA e dos demais indicadores deste site, a SELIC é divulgada **anualizada (% ao ano, base 252 dias úteis)**. Não representa a variação de um único mês, e sim a taxa em vigor no período.

O Copom se reúne a cada cerca de 45 dias e pode rever a taxa. Entre reuniões, o valor permanece estável; por isso, várias linhas consecutivas da tabela podem repetir o mesmo número.

A versão exibida aqui corresponde à série SGS 4189 do Banco Central — Selic acumulada no mês, anualizada base 252.

## Para que serve

- **Política monetária**: o Banco Central sobe a Selic para combater inflação e baixa para estimular a economia
- **Renda fixa**: títulos públicos como Tesouro Selic são remunerados pela taxa
- **Custo do crédito**: empréstimos, financiamentos e cartão de crédito têm custo influenciado pela Selic
- **Caderneta de poupança**: quando a Selic está acima de 8,5% a.a., a poupança rende 0,5% ao mês mais TR; abaixo disso, rende 70% da Selic mais TR

## Fonte

Dados obtidos da série 4189 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
```

**SEO:**

- `meta_title`: `SELIC - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje`
- `meta_description`: `SELIC de {month_name}/{year}: {value}% ao ano. Taxa básica de juros do Banco Central, anualizada base 252. Histórico completo da Selic desde 1986.`

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
- **IGP-M**: coleta entre o dia 21 do mês anterior ao dia 20 do mês de referência

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

Arquivo: `pipeline/db/migrations/002_seed_phase1_indicators.sql`

```sql
INSERT INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description
) VALUES
(
    'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',  -- UUID fixo para idempotência
    'IPCA',
    'ipca',
    'IPCA - Índice Nacional de Preços ao Consumidor Amplo',
    'Indicador oficial de inflação do Brasil. Calculado pelo IBGE, mede a variação dos preços de produtos e serviços para famílias com renda entre 1 e 40 salários mínimos.',
    '## O que é o IPCA ...',  -- conteúdo completo do markdown
    'inflacao',
    'percent',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/estatisticas/indecoreestrut',
    'bcb_sgs',
    '{"series_id": 433}',
    '1980-01-01',
    10,
    1,
    'IPCA - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'IPCA de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Tabela histórica completa desde 1980.'
),
(
    'b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e',
    'CDI',
    'cdi',
    'CDI - Certificado de Depósito Interbancário',
    'Taxa de juros média dos empréstimos entre bancos. Referência principal para investimentos de renda fixa e cálculo de rentabilidade no Brasil.',
    '## O que é o CDI ...',
    'juros',
    'percent',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/',
    'bcb_sgs',
    '{"series_id": 4391}',
    '1986-08-01',
    1,
    1,
    'CDI - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'CDI mensal de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico completo do CDI desde 1986.'
),
(
    'c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f',
    'TR',
    'tr',
    'TR - Taxa Referencial',
    'Taxa usada para correção monetária da poupança, FGTS e financiamentos imobiliários no Brasil. Calculada e divulgada diariamente pelo Banco Central.',
    '## O que é a TR ...',
    'correcao_monetaria',
    'percent',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/',
    'bcb_sgs',
    '{"series_id": 226}',
    '1991-03-01',
    1,
    1,
    'TR - Taxa Referencial - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'TR de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico da Taxa Referencial desde 1991.'
);
```

> Os UUIDs estão fixos na seed para que reaplicações da migration sejam idempotentes (`INSERT OR IGNORE` ou `ON CONFLICT DO NOTHING`). Os textos longos completos vão expandidos no arquivo SQL real.

## Smoke test pós-implantação

Após o setup inicial:

```bash
python -m pipeline.cli backfill IPCA
python -m pipeline.cli backfill CDI
python -m pipeline.cli backfill TR
python -m pipeline.cli build
python -m pipeline.cli deploy
```

Validações:

1. SQLite tem ~540 valores para IPCA (45 anos × 12 meses), ~480 para CDI, ~420 para TR
2. JSONs gerados em `site/data/` para cada um
3. PNGs gerados em `site/public/charts/`
4. Site no ar em `https://indicadoreseconomicoshoje.com.br/ipca/`
