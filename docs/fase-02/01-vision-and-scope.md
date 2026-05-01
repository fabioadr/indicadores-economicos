# 01 — Visão e Escopo da Fase 2

## Posicionamento

A Fase 1 entregou um MVP funcional com 3 indicadores (IPCA, CDI, TR) servidos a partir de um pipeline automatizado. A Fase 2 **completa o catálogo dos principais indicadores brasileiros** e **introduz a primeira camada de interatividade** no site.

## Objetivos da Fase 2

1. **Cobertura**: o usuário deve encontrar no site os indicadores mais consultados em decisões cotidianas — inflação (IPCA, IPCA-15, IGP-M, IGP-DI, INPC, INCC-M) e juros (SELIC, CDI já feito).
2. **Diversidade de fontes**: introduzir um segundo conector real (IBGE SIDRA), validando que o plugin pattern funciona.
3. **Filtros de tabela**: permitir que o usuário recorte a série histórica por período (12m, 24m, 5 anos, total) sem recarregar a página.
4. **Comparações**: oferecer visualizações comparando indicadores afins (ex: "Inflação no Brasil" comparando IPCA, IGP-M, INPC).
5. **Operação remota mais flexível**: agendamento configurável via Telegram, evitando depender do crontab para mudanças de horário.

## O que a Fase 2 É

- Extensão do MVP existente, **sem reescritas**
- 6 novos indicadores no catálogo
- 1 novo conector (IBGE SIDRA)
- 1 página nova (`/comparar/`) com PNGs comparativos
- Astro Islands pontuais para filtros de tabela
- Comandos novos no bot para agendamento

## O que a Fase 2 NÃO é

| Não é | Por quê |
|---|---|
| Revisão arquitetural | Stack continua a mesma; mudanças são adições, não substituições |
| Conector FGV nativo | Indicadores FGV (IGP-M, INCC, etc.) virão via espelho do BCB SGS — ver decisão abaixo |
| Calculadora de rentabilidade | Continua na Fase 3 |
| Gráficos interativos no detalhe do indicador | Continua na Fase 3 (Chart.js no cliente) |
| Comparação livre escolhida pelo usuário | Comparações são **pré-renderizadas** em PNG; livre-escolha é Fase 3 |
| Indicadores diários (câmbio, bolsa) | Fora de escopo permanente |
| Login, comentários, newsletter | Fora de escopo permanente |
| Multi-linguagem | Fora de escopo permanente |

## Decisões explicitadas

### Decisão 1: usar BCB SGS como espelho para indicadores FGV em vez de construir conector FGV nativo

**Contexto**: o backlog da Fase 1 listava "FGV connector" como item da Fase 2.

**Decisão**: **não construir** conector FGV nativo na Fase 2. Usar o espelhamento do BCB SGS para IGP-M (série 189), IGP-DI (190) e INCC-M (192).

**Motivo**:
- FGV não publica API pública estável; alternativas seriam scraping de portalibre.fgv.br ou parsing de CSV — ambas frágeis
- BCB espelha de forma confiável as séries FGV principais e tem SLA implícito alto
- Construir e manter um conector frágil tem custo desproporcional ao benefício
- Se algum dia o BCB parar de espelhar (improvável) ou precisarmos de granularidade FGV (ex: IPA-DI por estágios de produção), avaliamos na Fase 3

**Risco aceito**: dependência de uma única fonte (BCB) para 5 dos 9 indicadores do site. Mitigação: monitoramento via bot Telegram; falha de coleta gera notificação imediata.

### Decisão 2: construir conector IBGE SIDRA mesmo com BCB espelhando IBGE

**Contexto**: BCB espelha IPCA (série 433) e INPC (série 188). Poderíamos pular o conector IBGE.

**Decisão**: **construir** o conector IBGE SIDRA na Fase 2, ainda que ele inicialmente colete apenas IPCA-15 (série SIDRA 3065) e o INPC (tabela 1736). IPCA permanece via BCB SGS para não quebrar a Fase 1.

**Motivo**:
- Validar empiricamente que o plugin pattern funciona com fonte heterogênea (estrutura de URL, paginação e formato bem diferentes do BCB)
- IBGE SIDRA dá granularidade que o BCB não tem (regiões metropolitanas, grupos de despesa) — capacidade reservada para Fase 3
- Reduzir o risco de ponto único de falha no longo prazo

### Decisão 3: introduzir JS mínimo no cliente (Astro Islands)

**Contexto**: a Fase 1 estabeleceu "zero JS" como princípio.

**Decisão**: introduzir Astro Islands **apenas** para filtros de período de tabela e seletores de ano. Nada mais.

**Motivo**:
- Filtros de período exigem renderização condicional sobre dados já carregados; fazer no servidor exigiria múltiplos snapshots da mesma página
- Astro Islands hidrata só os componentes interativos, mantendo o resto do HTML estático
- O JS adicional é vanilla (sem framework) e cabe em <2KB minified
- O princípio "static-first" continua intacto; o que mudou é "zero JS no cliente" → "JS mínimo no cliente, justificado por feature, sem framework"

### Decisão 4: comparações pré-renderizadas em vez de interativas

**Contexto**: backlog dizia "Comparação entre indicadores no mesmo gráfico" sem especificar interatividade.

**Decisão**: criar uma página `/comparar/` que lista **comparações curadas pré-renderizadas em PNG**. Cada comparação é uma combinação de indicadores afins (ex: "Inflação oficial: IPCA vs INPC vs IGP-M"). O pipeline gera os PNGs no build.

**Motivo**:
- Mantém o site 100% estático nas páginas de comparação
- Combinações curadas são mais úteis ao público leigo do que escolha livre
- Evita explosão combinatória (9 indicadores tomados 2 a 2 já dá 36 combinações)
- Reusa o `charts.py` existente sem alterar o pipeline radicalmente

## Indicadores adicionados na Fase 2

| Code | Slug | Categoria | Fonte (Fase 2) | Série/Tabela |
|---|---|---|---|---|
| SELIC | selic | juros | BCB SGS | 4189 |
| IGPM | igp-m | inflacao | BCB SGS (espelhando FGV) | 189 |
| IGPDI | igp-di | inflacao | BCB SGS (espelhando FGV) | 190 |
| INPC | inpc | inflacao | BCB SGS (espelhando IBGE) | 188 |
| INCCM | incc-m | construcao_civil | BCB SGS (espelhando FGV) | 192 |
| IPCA15 | ipca-15 | inflacao | IBGE SIDRA | tabela 3065 |

> Os `series_id` do BCB devem ser **confirmados via subagent `bcb-research`** antes de cada implementação; valores acima são referência consolidada mas a fonte oficial deve sempre ser consultada.

> Nova categoria: `construcao_civil` (apenas INCC-M na Fase 2; antecipa o agrupamento sugerido na arquitetura original).

## Métricas de sucesso

| Métrica | Meta |
|---|---|
| Lighthouse mobile (todas as páginas) | ≥ 95 em todas as 4 categorias |
| Tempo de filtro de período (cliente) | < 100ms |
| Tamanho do JS no cliente (gzipped) | < 5KB |
| Indicadores com coleta automatizada estável | 9 |
| Tempo médio de manutenção operacional | continuar abaixo de 1h/mês |

## Definition of Done da Fase 2

- [ ] 6 indicadores novos publicados em produção, com séries históricas completas
- [ ] Conector IBGE SIDRA implementado, testado e em uso por pelo menos um indicador
- [ ] Página `/comparar/` no ar com pelo menos 3 comparações curadas
- [ ] Filtros de período funcionando em todas as páginas de detalhe de indicador
- [ ] Telegram com comandos `/agendamento` para alterar cron via mensagem
- [ ] Lighthouse mobile ≥ 95 nas 4 categorias em todas as páginas
- [ ] Cron rodando estável por 7 dias após deploy
- [ ] README atualizado com a documentação da Fase 2
