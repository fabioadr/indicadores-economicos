# Roadmap — Indicadores Econômicos Hoje

Próximos passos de evolução da aplicação. Documento **vivo**: reordenar por
demanda, mover itens para uma fase com spec própria quando entrarem em execução.
Cada item traz a motivação e a âncora no que o projeto já declarou.

Os princípios não mudam: static-first, SQLite local como fonte da verdade,
plugin pattern, idempotência, fail loud, free tier. Itens que ferem esses
princípios estão em **Fora de escopo permanente** no fim.

## Legenda de status

- **Pronto para spec** — escopo claro, sem bloqueio; falta só detalhar e executar
- **Candidato** — já citado nos docs como "se houver demanda"; validar antes
- **Exploratório** — ideia com valor, mas precisa de decisão de produto/arquitetura

## 1. Calendário e divulgação (evolui a Fase 4)

- **Alerta de atraso no Telegram** — *Pronto para spec*. Notificar quando um
  indicador passa da data prevista de divulgação sem dado novo. A âncora existe
  desde a Fase 1 (`docs/fase-01/07-telegram-bot.md`: "Avisar se passou X dias
  além do `expected_release_day` sem dado novo") e agora é barato: já temos
  `next_release` e a tabela `release_dates`. Reusar o padrão fail-soft de
  `pipeline/bot/notifications`.
- **Lembrete proativo no dia da divulgação** — *Candidato*. Mensagem no chat
  quando um indicador tem release oficial previsto para hoje (deriva de
  `release_dates`).
- **Datas oficiais para FGV e BCB** — *Candidato*. Hoje IGP-M/DI, INCC-M (FGV) e
  SELIC/CDI/TR usam estimativa (ver "Fora de escopo" em
  `docs/fase-04/00-README.md`). Quando houver fonte confiável, persistir em
  `release_dates` com `source` próprio — a estrutura já suporta. A UI já
  distingue `official` de `estimated`.
- **Exportar calendário (.ics) / "adicionar à agenda"** — *Exploratório*. Gerar
  um arquivo ICS estático a partir de `calendar.json` para assinatura.

## 2. Catálogo de indicadores

- **Mais indicadores em categorias existentes** — *Pronto para spec*. A Fase 2
  deixou `construcao_civil` com só o INCC-M e a Fase 3 deixou `atividade` com só
  a PIM-PF, ambos "receberá outros indicadores em fases futuras"
  (`docs/CLAUDE-DETAILS.md`). Candidatos naturais: PIB (atividade), PNAD/
  desemprego (atividade). Fluxo já existe: skill `add-indicator`.
- **Páginas "em breve" para indicadores propostos** — *Pronto para spec*.
  Publicar uma landing por indicador ainda não coletado (ex.: IPC-Fipe, PIM-PF
  do catálogo da Fase 3, PIB, PNAD) num estado "em breve" — explicação do que é,
  fonte, e sinal de interesse (evento GA e/ou "avise-me") — **antes** de
  construir o conector e fazer backfill. Objetivo: medir demanda real de busca/
  visitas para priorizar o catálogo com dado, não palpite. Mantém static-first:
  modelar como um estado do indicador (ex.: `status = 'coming_soon'`, sem série
  nem chart) e gerar a página via `getStaticPaths`, reaproveitando layout,
  categoria e SEO. Cuidado de SEO: a página precisa ter conteúdo útil de verdade
  (não placeholder vazio) para não virar thin content. **Spec pronta:**
  `docs/fase-05/00-README.md` (inclui o plano de medição GA4 + Search Console).
- **Conector FGV nativo** — *Exploratório*. Hoje os índices FGV entram via
  espelho no BCB SGS (decisão explícita da Fase 2 de não construir conector FGV).
  Reavaliar se/quando o espelho ficar instável ou faltar série. Mantém o plugin
  pattern (`pipeline/connectors/`).

## 3. Calculadoras

- **Calculadora de rentabilidade / investimento (SELIC, CDI)** — *Candidato*.
  Citada em dois lugares como candidata pós-Fase 3 (`docs/CLAUDE-DETAILS.md`:
  "calculadora de investimento é Fase 4 candidata"; `docs/fase-01/01-product-
  vision.md`). Reusaria a infra de calculadora da Fase 3 (`site/src/components/
  calculator/`, flag no DB, skill `add-calculator`), mas a lógica é diferente da
  correção monetária — precisa de spec própria.

## 4. Comparações

- **`/comparar/` com escolha livre de indicadores** — *Candidato*. A Fase 3
  manteve só grupos curados; escolha livre foi explicitamente adiada
  ("Fica para Fase 4 candidata se houver demanda", `docs/fase-03/01-vision-and-
  scope.md`). Exige decidir o trade-off de gerar dados/charts sob demanda sem
  abrir mão do static-first (ex.: client-side a partir dos JSONs já publicados).

## 5. SEO e descoberta

- **JSON-LD para o calendário e datas de divulgação** — *Exploratório*. Marcar a
  página `/calendario/` e as datas de próxima divulgação com schema.org para
  enriquecer resultados de busca, no espírito do JSON-LD Dataset já usado.

## 6. Internacionalização (i18n) — inglês e espanhol

- **Site multi-idioma** — *Exploratório (precisa de spec dedicada antes de
  executar)*. **Revisão de decisão de produto:** multi-linguagem estava como
  "fora de escopo permanente" (Fase 3), mas o GA mostra tráfego internacional
  relevante — provavelmente acadêmicos e analistas fora do Brasil, e as fontes
  oficiais (BCB/IBGE/FGV) não publicam esses dados em outras línguas, o que abre
  uma lacuna que o site pode ocupar. Prioridade: **inglês** (primordial) e
  **espanhol** (afinidade LATAM); `pt-BR` permanece o idioma padrão/canônico.

  Não é "traduzir strings" — é uma decisão de arquitetura e SEO que precisa ser
  muito bem pensada. Pontos a resolver na spec, **sem ferir o static-first**:

  - **Estratégia de URL**: subdiretório (`/en/`, `/es/`) é o que melhor casa com
    o site estático e o i18n nativo do Astro. Evitar subdomínio/ccTLD pelo custo
    de infra e autoridade fragmentada.
  - **SEO multilíngue (o ponto crítico)**: `hreflang` recíproco entre as versões
    + `x-default`, `<link rel="canonical">` por idioma, sitemaps por locale, e
    metadados/JSON-LD traduzidos. Tradução **genuína** — máquina sozinha vira
    thin/duplicate content e pode penalizar o domínio inteiro.
  - **Conteúdo a traduzir**: o caro é o `long_description` (markdown por
    indicador, hoje só em pt-BR no DB/migrations). Decidir o modelo de
    persistência (colunas/tabela por locale vs. arquivos de tradução) antes de
    escalar — mexe no schema e no builder.
  - **Formatação localizada**: números e datas hoje são `pt-BR` fixo em
    `site/src/lib/format.ts`; precisa virar locale-aware.
  - **Operação**: o conteúdo de dados (séries) é idioma-neutro; o esforço
    recorrente é a tradução de descrições novas — pesar no fluxo `add-indicator`.

  Recomendação: rodar um MVP só com a home + uma categoria + um indicador em
  inglês para medir SEO/engajamento antes de traduzir o catálogo inteiro.

## Fora de escopo permanente

Reafirmando o que os docs já fixam — não entram no roadmap:

- Login, comentários, newsletter
  (`docs/fase-03/01-vision-and-scope.md`) — *nota: multi-linguagem saiu desta
  lista e virou a seção 6 acima, por decisão de produto baseada no tráfego do GA*
- Dados em tempo real: câmbio, bolsa, cripto
  (`docs/fase-01/01-product-vision.md`)
- SSR/SPA, frameworks JS no cliente, Docker, PostgreSQL, ORM
  (`docs/CLAUDE-DETAILS.md`)
