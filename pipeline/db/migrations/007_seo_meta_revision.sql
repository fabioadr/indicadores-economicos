-- 007 — Revisão de SEO: títulos e meta descriptions orientados a "X hoje"
--
-- Motivação (ver docs/SEO.md):
--   A análise de Search Console (YTD 2026) mostrou que a família de consultas
--   "X hoje" (cdi hoje, ipca hoje, inflação hoje...) tem alto volume mas
--   ranqueia mal (posição 40-70), enquanto "X {mês}/{ano}" já converte
--   (posição 8-12). O título antigo ("X - Tabela atualizada {month}/{year}")
--   não continha o termo "hoje" nem o valor corrente, perdendo a família OURO.
--
--   Esta migration aplica a fórmula decidida, capturando "X hoje" + valor SEM
--   abandonar o padrão datado que já converte:
--     {Label} hoje: {value}% em {month_name}/{year} — tabela e histórico | <marca>
--   As variáveis {value}/{last_12m}/{month_name}/{year} continuam sendo
--   interpoladas no build (site/src/pages/[slug].astro), mantendo o frescor.
--
--   UPDATE é naturalmente idempotente; o runner (_migrations) ainda garante
--   execução única por nome de arquivo.

-- Inflação -------------------------------------------------------------------

UPDATE indicators SET
  meta_title = 'IPCA hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'IPCA hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e série histórica completa do IPCA desde 1980.',
  updated_at = datetime('now')
WHERE code = 'IPCA';

UPDATE indicators SET
  meta_title = 'IPCA-15 hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'IPCA-15 hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Prévia oficial do IPCA (IBGE): tabela atualizada e histórico.',
  updated_at = datetime('now')
WHERE code = 'IPCA15';

UPDATE indicators SET
  meta_title = 'INPC hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'INPC hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e histórico completo do INPC desde 1979.',
  updated_at = datetime('now')
WHERE code = 'INPC';

UPDATE indicators SET
  meta_title = 'IGP-M hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'IGP-M hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e histórico completo do IGP-M desde 1989.',
  updated_at = datetime('now')
WHERE code = 'IGPM';

UPDATE indicators SET
  meta_title = 'IGP-DI hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'IGP-DI hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e histórico completo do IGP-DI desde 1944.',
  updated_at = datetime('now')
WHERE code = 'IGPDI';

-- Juros ----------------------------------------------------------------------

UPDATE indicators SET
  meta_title = 'CDI hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'CDI hoje: {value}% no mês de {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e histórico completo do CDI desde 1986.',
  updated_at = datetime('now')
WHERE code = 'CDI';

-- SELIC é anualizada (% a.a.) e não acumula (aggregation_mode='none'): não usar
-- {last_12m}, que seria NULL e renderizaria como "—".
UPDATE indicators SET
  meta_title = 'SELIC hoje: {value}% ao ano em {month_name}/{year} — histórico | Indicadores Econômicos Hoje',
  meta_description = 'SELIC hoje: {value}% ao ano em {month_name}/{year}. Taxa básica de juros do Banco Central (base 252). Tabela atualizada e histórico da Selic desde 1986.',
  updated_at = datetime('now')
WHERE code = 'SELIC';

UPDATE indicators SET
  meta_title = 'Selic acumulada hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'Selic acumulada no mês hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela e histórico da Selic mensal desde 1986.',
  updated_at = datetime('now')
WHERE code = 'SELICAC';

-- Correção monetária ---------------------------------------------------------

UPDATE indicators SET
  meta_title = 'TR hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'TR (Taxa Referencial) hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Tabela atualizada e histórico da TR desde 1991.',
  updated_at = datetime('now')
WHERE code = 'TR';

-- Construção civil -----------------------------------------------------------

UPDATE indicators SET
  meta_title = 'INCC-M hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje',
  meta_description = 'INCC-M hoje: {value}% em {month_name}/{year}. Acumulado em 12 meses: {last_12m}%. Custo da construção civil: tabela atualizada e histórico desde 1989.',
  updated_at = datetime('now')
WHERE code = 'INCCM';
