-- 004 — Phase 2 seed indicators (SELIC, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15)
-- UUIDs v4 fixos por indicador. INSERT OR IGNORE garante idempotência.
--
-- Nota SELIC: a série SGS 4189 retorna a Selic anualizada base 252 (% a.a.),
-- não variação mensal como os demais indicadores. Os textos abaixo deixam isso
-- explícito.

INSERT OR IGNORE INTO indicators (
    id, code, slug, name, short_description, long_description,
    category, unit, frequency, source_name, source_url,
    connector_type, connector_config, inception_date, expected_release_day,
    active, meta_title, meta_description
) VALUES
(
    'ae141e8e-9c39-4cdb-973f-a18a7f06f11a',
    'SELIC',
    'selic',
    'SELIC - Taxa Básica de Juros (anualizada)',
    'Taxa básica de juros da economia brasileira, definida pelo Copom. Expressa em % ao ano (anualizada base 252) e revista a cada reunião do Copom, aproximadamente a cada 45 dias.',
    '## O que é a SELIC

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

Dados obtidos da série 4189 do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.',
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
    'SELIC de {month_name}/{year}: {value}% ao ano. Taxa básica de juros do Banco Central, anualizada base 252. Histórico completo da Selic desde 1986.'
),
(
    'b62e61e7-3c18-4a22-8eb2-a4785c1b9d0c',
    'IGPM',
    'igp-m',
    'IGP-M - Índice Geral de Preços do Mercado',
    'Índice de inflação calculado pela FGV. Conhecido como "inflação do aluguel", é amplamente usado para reajuste de contratos, especialmente imobiliários.',
    '## O que é o IGP-M

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

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 189), que replica os valores oficiais publicados pela FGV.',
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
    '4d51ac50-018c-4c0e-86e7-766f854f6fa1',
    'IGPDI',
    'igp-di',
    'IGP-DI - Índice Geral de Preços - Disponibilidade Interna',
    'Índice de inflação da FGV, similar ao IGP-M mas com período de coleta dentro do mês civil. Usado em contratos públicos e análise histórica de longo prazo.',
    '## O que é o IGP-DI

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

Espelho do Banco Central do Brasil (série SGS 190), replicando os valores oficiais publicados pela FGV.',
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
    '9e1000c1-1bb7-4e34-8384-ee789a567759',
    'INPC',
    'inpc',
    'INPC - Índice Nacional de Preços ao Consumidor',
    'Índice oficial de inflação para famílias de baixa renda, calculado pelo IBGE. É a referência principal para reajustes de salários e benefícios trabalhistas.',
    '## O que é o INPC

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

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 188), que replica os valores oficiais publicados pelo IBGE.',
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
    '5f7c5790-fc7d-4aa4-8e56-16249aa3ef8a',
    'INCCM',
    'incc-m',
    'INCC-M - Índice Nacional do Custo da Construção (Mercado)',
    'Índice da FGV que mede a evolução dos custos da construção civil habitacional no Brasil. Usado em contratos de financiamento imobiliário durante a fase de obra.',
    '## O que é o INCC-M

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

Esta página obtém os dados pelo espelho do Banco Central do Brasil (série SGS 192), que replica os valores oficiais publicados pela FGV.',
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
    'f2fef5bc-a9af-400a-9dfa-601b06cb5695',
    'IPCA15',
    'ipca-15',
    'IPCA-15 - Índice de Preços ao Consumidor Amplo - 15',
    'Prévia do IPCA, calculada pelo IBGE com janela de coleta antecipada. Sai antes do IPCA oficial e é usada como sinal antecipado da inflação do mês.',
    '## O que é o IPCA-15

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

Dados obtidos da tabela 7060 do SIDRA/IBGE, variável 355 (variação mensal), agregado Brasil.',
    'inflacao',
    'percent',
    'monthly',
    'IBGE',
    'https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo-15.html',
    'ibge_sidra',
    '{"tabela": 7060, "variavel": 355, "localidade": "N1[all]"}',
    '2000-05-01',
    25,
    1,
    'IPCA-15 - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje',
    'IPCA-15 de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Prévia oficial do IPCA, do IBGE.'
);
