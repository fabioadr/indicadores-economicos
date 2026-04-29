# 01 — Visão de Produto

## Problema

Brasileiros leigos precisam consultar indicadores econômicos (inflação, juros, correção monetária) e os encontram dispersos em sites institucionais densos (BCB, IBGE, FGV). Os portais financeiros existentes ou exigem login, ou misturam o dado com excesso de propaganda, ou usam linguagem técnica.

## Proposta

Site agregador minimalista, rápido, com tabelas históricas e gráficos limpos. Linguagem acessível. Atualização automática via fontes oficiais.

## Público-alvo

- **Primário**: pessoa física consultando para reajuste de aluguel, FGTS, financiamento, salário, simulação de aplicação
- **Secundário**: profissionais (contadores, advogados, jornalistas) precisando de uma referência rápida

## Métricas de sucesso

| Métrica | Meta inicial |
|---|---|
| Tempo de carregamento (LCP) | < 1s |
| Tráfego orgânico mensal | crescer mês a mês (sem meta absoluta) |
| Posição no Google para `<indicador> hoje` | top 10 em 6 meses |
| Tempo de manutenção operacional | < 1h por mês |

## O que o sistema É

- Site público estático com séries históricas de indicadores brasileiros
- Pipeline local que coleta, consolida e publica automaticamente
- Bot Telegram para operação remota

## O que o sistema NÃO é

| Não é | Por quê |
|---|---|
| Fonte primária de dados | Apenas agrega fontes oficiais |
| Sistema financeiro | Sem carteira, sem alertas, sem trading |
| Dados em tempo real | Câmbio, bolsa e cripto estão fora de escopo |
| Plataforma com login | Site público é leitura anônima |
| API pública | Apenas site estático |
| Calculadora avançada (Fase 1) | Calculadora de rentabilidade fica para Fase 3 |
| Conteúdo editorial | Sem blog, sem análises, sem opinião |

## Disclaimer obrigatório no site

Em rodapé de todas as páginas e em destaque na página inicial:

> Os dados apresentados neste site são coletados de fontes públicas oficiais (Banco Central do Brasil, IBGE, FGV) e replicados de forma automatizada. Indicadores Econômicos Hoje não é uma instituição financeira nem fonte primária de dados. Sempre confirme valores na fonte oficial antes de tomar decisões financeiras ou jurídicas.

## Fora de escopo permanente

- Comentários de usuários
- Newsletter
- Pop-ups, paywall, login social
- Anúncios intrusivos (pode haver Google AdSense discreto se for necessário monetizar, mas não na Fase 1)
- App mobile nativo
- Versão em outros idiomas
