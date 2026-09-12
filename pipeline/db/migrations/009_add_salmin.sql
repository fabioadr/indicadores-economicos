-- 009 — Add SALMIN indicator
-- UUID v4 fixo. INSERT OR IGNORE garante idempotência.
-- Série SGS 1619 a partir de jul/1994: antes disso a mesma série mistura moedas.
-- expected_release_day nulo: o piso muda por decreto, não tem divulgação mensal.

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description, aggregation_mode
) VALUES (
    'bdebcb49-6e24-4477-aa95-a7b801180184',
    'SALMIN',
    'salario-minimo',
    'Salário mínimo',
    'Piso salarial nacional vigente, em reais. Valor mensal, por dia e por hora, com o histórico por vigência desde 1994.',
    '## O que é o salário mínimo

O salário mínimo é o menor valor mensal que pode ser pago a um trabalhador no Brasil. É fixado por decreto do governo federal e vale em todo o país. A série desta página é o piso nacional vigente, em reais, desde julho de 1994 (Plano Real).

O valor muda em degraus — em geral uma vez por ano, em 1º de janeiro — e se repete nos demais meses. Por isso a tabela mostra uma linha por vigência, não doze meses iguais.

O valor diário é o mensal dividido por 30. O valor por hora usa a jornada de 44 horas semanais: mensal dividido por 220. São as bases usuais da CLT para mensalista; não são séries separadas.

## Para que serve

- **Consulta do piso vigente**: quanto vale o mínimo hoje, por dia e por hora
- **Reajuste**: quanto o último decreto acrescentou, em reais e em percentual
- **Histórico**: acompanhar a escada nominal desde 1994
- **Referência de benefícios**: o piso nacional é também o valor mínimo de aposentadorias, pensões e do Benefício de Prestação Continuada (BPC)

A política de valorização do piso usa o [INPC](/inpc/) (inflação das famílias de menor renda) e o crescimento do PIB de dois anos antes, com teto legal. O INPC mede a variação de preços; o salário mínimo é um valor em reais. Não são comparáveis no mesmo gráfico.

Cinco estados podem fixar pisos regionais acima do nacional. Onde a faixa estadual fica abaixo do piso federal, vale o nacional. Esses pisos não entram nesta série.

## Fonte

Dados obtidos da série 1619 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil: salário mínimo nacional vigente, em reais. A série começa em 1990 no SGS; aqui o histórico público parte de julho de 1994, quando o valor já está em reais do Plano Real.',
    'trabalho',
    'brl',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/',
    'bcb_sgs',
    '{"series_id": 1619}',
    '1994-07-01',
    NULL,
    1,
    'Salário mínimo hoje: {value} em {month_name}/{year} | Indicadores Econômicos Hoje',
    'Salário mínimo de {month_name}/{year}: {value}. Reajuste em 12 meses: {last_12m}%. Valor diário, por hora e histórico desde 1994.',
    'level'
);
