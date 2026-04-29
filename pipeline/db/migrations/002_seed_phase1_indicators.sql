-- 002 — Phase 1 seed indicators (IPCA, CDI, TR)
-- UUIDs are fixed (see docs/08-indicators-catalog.md) so INSERT OR IGNORE
-- keeps this migration idempotent even outside the _migrations runner.

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description
) VALUES
(
    'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
    'IPCA',
    'ipca',
    'IPCA - Índice Nacional de Preços ao Consumidor Amplo',
    'Indicador oficial de inflação do Brasil. Calculado pelo IBGE, mede a variação dos preços de produtos e serviços para famílias com renda entre 1 e 40 salários mínimos.',
    '## O que é o IPCA

O IPCA — Índice Nacional de Preços ao Consumidor Amplo — é o indicador oficial de inflação do Brasil. É calculado e divulgado mensalmente pelo IBGE (Instituto Brasileiro de Geografia e Estatística).

## Como é calculado

O IPCA mede a variação de preços de uma cesta de produtos e serviços consumidos por famílias com renda entre 1 e 40 salários mínimos, em 13 áreas urbanas (regiões metropolitanas, Brasília e Goiânia).

A pesquisa de preços ocorre durante todo o mês de referência. O resultado é divulgado entre os dias 7 e 12 do mês seguinte.

## Para que serve

- **Meta de inflação**: o Banco Central usa o IPCA como referência para sua política monetária e meta oficial de inflação.
- **Reajustes**: muitos contratos, salários e benefícios são corrigidos pelo IPCA.
- **Análises econômicas**: é a referência mais usada para discutir inflação no Brasil.

## Fonte

Os dados desta página são obtidos da API do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil, série 433.',
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
    '## O que é o CDI

O CDI — Certificado de Depósito Interbancário — é a taxa média de juros das operações de empréstimo de um dia entre os bancos. Esse mercado existe porque, ao final de cada dia, alguns bancos têm sobra e outros têm falta de caixa, e fazem operações de curtíssimo prazo entre si.

## Como funciona

A taxa CDI acompanha de perto a Selic, a taxa básica de juros definida pelo Banco Central. Em geral, o CDI fica ligeiramente abaixo da Selic.

A versão mensal acumula as taxas diárias do mês. É divulgada no primeiro dia útil do mês seguinte.

## Para que serve

- **Benchmark de renda fixa**: muitos investimentos (CDBs, fundos DI, LCIs, LCAs) são remunerados como percentual do CDI (ex: "120% do CDI").
- **Custo de operações**: empréstimos e financiamentos entre bancos têm o CDI como referência.
- **Comparação de aplicações**: ao comparar duas aplicações de renda fixa, o CDI é a régua mais usada.

## Fonte

Dados obtidos da série 4391 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.',
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
    '## O que é a TR

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

Dados obtidos da série 226 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.',
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
