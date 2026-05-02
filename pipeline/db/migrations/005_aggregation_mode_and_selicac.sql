-- 005 — Aggregation mode + novo indicador SELICAC
--
-- Motivação:
--   - SELIC (série SGS 4189) retorna a Selic anualizada (% a.a.). Compor
--     geometricamente esses valores como se fossem variações mensais produz
--     YTD/12m/24m/since_inception completamente errados. Marcar
--     `aggregation_mode='none'` para que essas colunas fiquem NULL.
--   - TR (série SGS 226) é diária; cada valor é a TR de um dia, mas a tabela
--     guarda ~30 valores por mês e a composição direta dos diários infla YTD
--     e last_12m. Marcar `aggregation_mode='compound_daily_to_monthly'` para
--     reduzir a 1 valor por mês (último do mês) antes de compor.
--   - Novo indicador SELICAC (Selic acumulada no mês, série 4390) cobre o uso
--     "% a.m." que faltava: agrega como CDI.

ALTER TABLE indicators
  ADD COLUMN aggregation_mode TEXT NOT NULL DEFAULT 'compound_monthly';

UPDATE indicators
   SET aggregation_mode = 'none',
       updated_at = datetime('now')
 WHERE code = 'SELIC';

UPDATE indicators
   SET aggregation_mode = 'compound_daily_to_monthly',
       updated_at = datetime('now')
 WHERE code = 'TR';

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description, aggregation_mode
) VALUES (
    '9b50b230-c5f2-4bfa-a8eb-b13edb88b73c',
    'SELICAC',
    'selic-acumulada',
    'Selic acumulada no mês',
    'Variação mensal da Selic acumulada (% no mês), publicada pelo Banco Central. Diferente da Selic anualizada, este indicador permite compor acumulados YTD e 12 meses, similar ao CDI.',
    '## O que é a Selic acumulada no mês

A Selic acumulada no mês é a expressão **mensal** da Taxa Selic Efetiva: representa, em percentual, quanto rendeu uma aplicação corrigida pela Selic ao longo de um mês cheio. É publicada pelo Banco Central como série SGS 4390.

Diferente da [SELIC anualizada](/selic/) — que é divulgada em % ao ano — a Selic acumulada vem em % ao mês. Por isso ela pode ser composta geometricamente para gerar acumulados YTD, 12 meses e de longo prazo, exatamente como o CDI.

## Selic acumulada vs SELIC anualizada vs CDI

- **SELIC anualizada (4189)**: taxa em vigor expressa em % a.a., base 252 dias úteis. Não acumula.
- **Selic acumulada no mês (4390 — esta página)**: variação mensal de fato, em % a.m. Acumula geometricamente.
- **CDI mensal (4391)**: taxa equivalente do mercado interbancário, em % a.m. Costuma andar levemente abaixo da Selic acumulada.

Para uma mesma janela de tempo, o produto geométrico das taxas mensais da 4390 deve coincidir, dentro do ruído de arredondamento, com o rendimento implícito da Selic anualizada do período.

## Para que serve

- **Tesouro Selic e fundos DI**: acompanhamento direto do rendimento mês a mês
- **Comparação histórica**: compor 12 meses para comparar com inflação acumulada
- **Estudos macro**: medir o custo real do crédito ao longo do tempo

## Fonte

Dados obtidos da série 4390 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.',
    'juros',
    'percent',
    'monthly',
    'Banco Central do Brasil',
    'https://www.bcb.gov.br/controleinflacao/historicotaxasjuros',
    'bcb_sgs',
    '{"series_id": 4390}',
    '1986-03-01',
    1,
    1,
    'Selic acumulada no mês - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'Selic acumulada no mês de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Histórico desde 1986 da Selic mensal.',
    'compound_monthly'
);
