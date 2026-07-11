-- 008 — Poupança + Mercado Imobiliário (P0)
--
-- Categorias novas: poupanca, mercado_imobiliario.
-- Unidades novas: brl_millions (nível em R$ milhões), index (índice).
-- aggregation_mode='level' para séries de estoque/fluxo/índice (variação %
-- derivada em ytd/last_12m/…); POUPREN é diária (% a.m.) e usa
-- compound_daily_to_monthly como a TR.

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description, aggregation_mode
) VALUES
(
    '4cd3b9e6-1477-48de-b5f4-1bffd02399f4',
    'POUPSAL',
    'poupanca-saldo',
    'Poupança - Saldo de depósitos (SBPE e rural)',
    'Saldo mensal dos depósitos de poupança no SBPE e na poupança rural, em R$ milhões. Mede o estoque total aplicado na caderneta.',
    '## O que é o saldo da poupança

O saldo de depósitos de poupança (série SGS 7836) é o estoque total aplicado na caderneta de poupança no Sistema Brasileiro de Poupança e Empréstimo (SBPE) e na poupança rural, expresso em milhões de reais correntes. É um indicador de **nível** (estoque), não uma taxa: o valor absoluto importa tanto quanto a variação percentual no tempo.

A poupança continua sendo o funding principal do crédito imobiliário no Brasil — boa parte das concessões de financiamento habitacional depende do volume captado nessa modalidade.

## Para que serve

- **Funding imobiliário**: acompanhar se o saldo cresce ou encolhe ajuda a antecipar pressão sobre o crédito habitacional
- **Poupança das famílias**: leitura do volume de recursos de baixo risco parado na caderneta
- **Comparação com crédito**: cruzar com concessões e saldo de financiamento imobiliário mostra a relação funding → crédito

## Fonte

Dados obtidos da série 7836 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: saldo mensal de depósitos de poupança — SBPE e rural.',
    'poupanca',
    'brl_millions',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/estatisticas/detalhamentoCategoria?codigo=4',
    'bcb_sgs',
    '{"series_id": 7836}',
    '1994-07-01',
    20,
    1,
    'Saldo da poupança hoje: {value} em {month_name}/{year} | Indicadores Econômicos Hoje',
    'Saldo da poupança (SBPE e rural) em {month_name}/{year}: {value}. Variação em 12 meses: {last_12m}%. Estoque mensal desde 1994.',
    'level'
),
(
    '7c8470ba-e718-4e31-8ab2-c03367b04984',
    'POUPREN',
    'poupanca-rentabilidade',
    'Poupança - Rentabilidade (depósitos a partir de 04/05/2012)',
    'Rentabilidade diária da caderneta de poupança no regime pós-2012, em % ao mês. Divulgada pelo Banco Central para cada data de aniversário do depósito.',
    '## O que é a rentabilidade da poupança

A série SGS 195 traz a rentabilidade no período dos depósitos de poupança feitos a partir de 4 de maio de 2012 — o regime atual de remuneração. O valor é expresso em **percentual ao mês** (% a.m.) e a frequência de divulgação é **diária** (uma taxa para cada data de aniversário).

Nesse regime, a regra depende do nível da Selic:

- Selic acima de 8,5% a.a.: 0,5% a.m. + TR
- Selic igual ou abaixo de 8,5% a.a.: 70% da Selic + TR

## Para que serve

- **Comparar rendimento**: ver quanto a poupança rendeu frente a CDI, Selic acumulada ou inflação
- **Simulações**: base para correção de saldos e planejamento de aplicações de baixo risco
- **Contexto do funding**: a atratividade relativa da poupança influencia o saldo (POUPSAL) e, indiretamente, o crédito imobiliário

## Fonte

Dados obtidos da série 195 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: depósitos de poupança a partir de 04.05.2012 — rentabilidade no período.',
    'poupanca',
    'percent',
    'daily',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/',
    'bcb_sgs',
    '{"series_id": 195}',
    '2012-05-04',
    1,
    1,
    'Rentabilidade da poupança hoje: {value}% em {month_name}/{year} | Indicadores Econômicos Hoje',
    'Rentabilidade da poupança (regime pós-2012) em {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Série diária desde maio/2012.',
    'compound_daily_to_monthly'
),
(
    '26dd1489-d8e7-4775-b3c7-7cb09614f814',
    'FINIMOB',
    'financiamento-imobiliario-concessoes',
    'Financiamento imobiliário - Concessões (PF)',
    'Concessões mensais de crédito imobiliário a pessoas físicas com recursos direcionados, em R$ milhões. Mede o fluxo de novas operações no período.',
    '## O que são as concessões de financiamento imobiliário

A série SGS 20704 registra as **concessões** (novas operações) de crédito com recursos direcionados para pessoas físicas na modalidade financiamento imobiliário total, em milhões de reais. Diferente do saldo (estoque), as concessões são um **fluxo**: quanto de crédito novo foi liberado no mês.

Esse fluxo depende em grande parte do funding da poupança (SBPE) e das condições de juros e preços de imóveis.

## Para que serve

- **Temperatura do crédito habitacional**: concessões em alta sinalizam mercado aquecido
- **Ligação poupança → crédito**: comparar com o saldo da poupança ajuda a ler a capacidade de funding
- **Ciclo do mercado imobiliário**: junto com preços (IVG-R) e custos de obra (INCC-M), forma o quadro de demanda e oferta

## Fonte

Dados obtidos da série 20704 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: concessões de crédito com recursos direcionados — PF — financiamento imobiliário total.',
    'mercado_imobiliario',
    'brl_millions',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/estatisticas/detailcreditostatistics',
    'bcb_sgs',
    '{"series_id": 20704}',
    '2011-03-01',
    25,
    1,
    'Concessões de financiamento imobiliário: {value} em {month_name}/{year} | Indicadores Econômicos Hoje',
    'Concessões de crédito imobiliário PF em {month_name}/{year}: {value}. Variação em 12 meses: {last_12m}%. Fluxo mensal desde 2011.',
    'level'
),
(
    '440f644b-7639-4d04-a2e4-a6cf56bd0bcc',
    'FINISAL',
    'financiamento-imobiliario-saldo',
    'Financiamento imobiliário - Saldo PF (taxas reguladas)',
    'Saldo da carteira de crédito imobiliário a pessoas físicas com taxas reguladas (recursos direcionados), em R$ milhões. Mede o estoque de financiamentos em aberto.',
    '## O que é o saldo de financiamento imobiliário

A série SGS 20611 traz o **saldo** (estoque) da carteira de crédito com recursos direcionados para pessoas físicas no financiamento imobiliário **com taxas reguladas**, em milhões de reais. É o volume ainda em aberto no fim do período — diferente das concessões, que medem só o fluxo do mês.

Atenção: cobre a fatia de **taxas reguladas**, não necessariamente o saldo imobiliário PF total do sistema.

Esse estoque é a contraparte natural do funding da poupança e um termômetro do endividamento habitacional das famílias.

## Para que serve

- **Estoque de crédito habitacional**: acompanhar o tamanho da carteira regulada
- **Funding vs crédito**: cruzar com saldo da poupança e concessões
- **Risco e ciclo**: saldos em expansão rápida em ambiente de juros altos merecem atenção

## Fonte

Dados obtidos da série 20611 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: saldo da carteira de crédito com recursos direcionados — PF — financiamento imobiliário com taxas reguladas.',
    'mercado_imobiliario',
    'brl_millions',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/estatisticas/detailcreditostatistics',
    'bcb_sgs',
    '{"series_id": 20611}',
    '2007-03-01',
    25,
    1,
    'Saldo de financiamento imobiliário: {value} em {month_name}/{year} | Indicadores Econômicos Hoje',
    'Saldo de crédito imobiliário PF (taxas reguladas) em {month_name}/{year}: {value}. Variação em 12 meses: {last_12m}%. Estoque desde 2007.',
    'level'
),
(
    'a52e2c0a-850a-40f6-82d6-c733c3f24eb7',
    'IVGR',
    'ivg-r',
    'IVG-R - Índice de Valores de Garantia de Imóveis Residenciais',
    'Índice do Banco Central que acompanha a valorização das garantias de imóveis residenciais financiados (base mar/2001 = 100). Proxy de preços no mercado imobiliário.',
    '## O que é o IVG-R

O IVG-R — Índice de Valores de Garantia de Imóveis Residenciais Financiados — é calculado pelo Banco Central a partir dos valores de garantia dos imóveis dados em financiamento habitacional. A base é março de 2001 = 100. É um indicador de **nível** (índice), cuja variação percentual no tempo funciona como proxy da trajetória de preços residenciais.

No segmento de **RE (Real Estate)**, o IVG-R complementa leituras de crédito (concessões e saldo) e de custo de obra (INCC-M): preços sobem, custo sobe, ou o crédito se expande?

## Para que serve

- **Preços residenciais**: acompanhar valorização implícita nas garantias financiadas
- **Preço vs custo**: comparar com INCC-M (e IGP-M) para ver se imóveis sobem mais que o custo de construir
- **Ciclo imobiliário**: ler junto com concessões e saldo de financiamento

## Fonte

Dados obtidos da série 21340 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: Índice de Valores de Garantia de Imóveis Residenciais Financiados (IVG-R).',
    'mercado_imobiliario',
    'index',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/estatisticas',
    'bcb_sgs',
    '{"series_id": 21340}',
    '2001-03-01',
    25,
    1,
    'IVG-R hoje: {value} em {month_name}/{year} | Indicadores Econômicos Hoje',
    'IVG-R em {month_name}/{year}: {value}. Variação em 12 meses: {last_12m}%. Índice de valorização de garantias residenciais desde 2001.',
    'level'
);
