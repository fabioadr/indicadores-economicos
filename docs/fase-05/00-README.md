# Documentação — Indicadores Econômicos Hoje · Fase 5

Spec de implementação do **catálogo "em breve"**: publicar páginas de
indicadores ainda não coletados para **medir demanda de busca** (via Search
Console + GA4) antes de investir em conector e backfill. Origem: item da seção 2
do `docs/ROADMAP.md`.

## Objetivo e princípio

Hoje priorizamos o catálogo por palpite. A página "em breve" inverte isso:
coloca o indicador na sua **URL final** `/{slug}/` com conteúdo útil, mede
interesse real de busca por algumas semanas e só então decide construir o
conector. Quando o indicador é promovido, a **URL não muda** — o ranking
acumulado é preservado.

Mantém os princípios do projeto: static-first, SQLite como fonte da verdade,
sem backend, plugin pattern, idempotência. A página "em breve" **não** tem
série, chart, tabela, calendário nem comparação — só conteúdo editorial + SEO +
um sinal de interesse.

Candidatos iniciais (já citados nos catálogos): **IPC-Fipe**, **PIM-PF**
(propostos na Fase 3), **PIB** e **PNAD/desemprego** (categoria `atividade`).

## Medição (responde "como medir a busca")

Os dois instrumentos já existem no site e são complementares:

### Search Console — demanda real de busca (sinal primário)

- O GSC só reporta URLs **existentes e indexáveis**; por isso a página "em breve"
  é o instrumento de medição. Ela torna `/{slug}/` elegível a impressões para
  buscas como "pib tabela", "pib série histórica".
- **Desempenho → filtrar por Página** (cada slug novo): ler **impressões**,
  **CTR**, **posição média** e as **consultas** que dispararam impressão.
- Comparar impressões/consultas entre os candidatos rankeia a demanda latente.
- **Inspeção de URL → Solicitar indexação** para cada página nova (acelera).
- Pré-sinal opcional: inspecionar as consultas que já caem nas páginas de
  categoria (ex.: `/atividade/`) — buscas por "PIB" podem já aparecer ali.
- Ressalva honesta: indexação + acúmulo de impressões leva ~2–6 semanas; o sinal
  é direcional, não instantâneo, e tende a crescer devagar (página sem dado atrai
  menos links).

### GA4 — comportamento e intenção (sinal secundário)

- `page_view` automático já segmenta por `page_path` (Engajamento → Páginas).
- **Evento de interesse**: botão "Avise-me quando publicar" dispara
  `gtag('event', 'coming_soon_interest', { indicator_code, indicator_slug })`.
  Marcar como **Key Event** no GA4 (vira conversão) e registrar
  `indicator_code`/`indicator_slug` como **dimensões personalizadas** (Admin)
  para agrupar no Explore.
- Opcional: `gtag('event', 'coming_soon_view', {...})` no load, para montar funil
  view → interest por indicador.
- Captura de e-mail (opcional, sem backend): link para um formulário externo
  (Google Forms/Tally) — só se quiser contatos reais; exige nota na política de
  privacidade. MVP fica só no evento GA4 (sem PII).

### Regra de decisão

Após ~4–6 semanas, rankear candidatos por
`impressões_GSC × CTR + eventos_interesse_GA4` e construir os campeões pelo fluxo
`add-indicator`. Opcional: dashboard no Looker Studio unindo GA4 + GSC por página.

## Modelo de dados

Migration nova `pipeline/db/migrations/007_indicator_status.sql`:

```sql
ALTER TABLE indicators
  ADD COLUMN status TEXT NOT NULL DEFAULT 'active';  -- 'active' | 'coming_soon'
```

Seed de cada indicador "em breve" (via subagent `migration-author`, reusando a
pesquisa de metadados do `add-indicator` — nome, descrições, fonte, SEO):

- `status = 'coming_soon'`, `active = 0` (exclui de coleta e do build de valores).
- `connector_type = 'none'`, `connector_config = '{}'`, `inception_date` placeholder
  (`'1900-01-01'`), `expected_release_day` NULL — nunca são coletados.
- `name`, `slug`, `category`, `short_description`, `long_description`,
  `source_name`, `source_url`, `meta_title`, `meta_description` preenchidos
  normalmente (é o conteúdo que vai medir SEO).

`active = 0` garante que `list_active_indicators` (coleta, build de valores,
calendário, comparações) ignore esses registros sem nenhuma mudança nesses
caminhos.

## Pipeline / build

`pipeline/db/connection.py`:

- `_INDICATOR_COLUMNS` + `_row_to_indicator` passam a incluir `status` (campo novo
  no dataclass `Indicator`, default `'active'`).
- Nova `list_coming_soon_indicators(conn)` → `WHERE status = 'coming_soon'
  ORDER BY code`.

`pipeline/core/builder.py`:

- Nova `write_coming_soon_index(indicators, out_dir, generated_at)` →
  `site/data/coming-soon.json`: array com o **conteúdo completo** de cada
  indicador `coming_soon` (`code, slug, name, category, short_description,
  long_description, source{name,url}, meta{title,description}`). Sem `latest`,
  `values`, `charts`. (Não há JSON por-slug; a página lê deste índice.)
- Chamar em `build()` no mesmo padrão de `calendar.json`/`groups.json`: sempre no
  caminho de sucesso; no caminho `no_changes`, só se o arquivo faltar (preserva o
  teste `test_build_no_changes_keeps_existing_groups_json`).
- **Gating:** como adicionar/editar um `coming_soon` não altera `last_collected_at`
  de nenhum indicador ativo, um `build` pode cair em `no_changes` e não reescrever
  um `coming-soon.json` já existente. Resolver com um flag novo
  `pipeline.cli build --force` que ignora `needs_rebuild` e regenera tudo
  (útil em geral). O fluxo de adicionar "em breve" termina com `build --force`.

`pipeline/cli.py`: adicionar `--force` ao subcomando `build` (repassa a
`builder.build(..., force=True)`; quando `force`, tratar todos os ativos como
`changed`).

## Site (Astro)

`site/src/lib/data.ts`:

- Tipo novo `ComingSoonEntry` (campos acima) + `loadComingSoon(): ComingSoonEntry[]`
  lendo `coming-soon.json` (retornar `[]` se o arquivo não existir, para não
  quebrar build antes do primeiro `coming-soon.json`).
- Acrescentar `status?: 'active' | 'coming_soon'` onde fizer sentido (não é
  obrigatório em `IndicatorSummary`, que continua só com ativos).

**Rota `/{slug}/` (`site/src/pages/[slug].astro`)** — a URL final desde já:

- `getStaticPaths` passa a **mesclar** `loadIndex().indicators` (ativos) +
  `loadComingSoon()` (em breve), com uma prop `comingSoon: boolean` e o `slug`.
- No corpo: se `comingSoon`, renderizar o **layout "em breve"** (sem
  `IndicatorHero`/charts/tabelas/relacionados-com-dado); senão, o fluxo atual.

**Componente novo `site/src/components/domain/ComingSoon.astro`**:

- Cabeçalho com `CategoryPill` + selo "Em breve"/"Em construção".
- `name`, `short_description`, bloco "O que é / Para que serve / Fonte" via
  `renderMarkdown(long_description)` (mesmo pipeline do detalhe).
- **CTA de interesse**: botão "Avise-me quando publicar" com um `is:inline`
  script mínimo (sem framework, <1KB) que chama
  `gtag('event', 'coming_soon_interest', { indicator_code, indicator_slug })`,
  troca o texto por uma confirmação ("Anotado — avisaremos por aqui") e
  desabilita reclique. Disparar também `coming_soon_view` no `DOMContentLoaded`
  (opcional).
- Link para a categoria e para indicadores já publicados (interligação interna
  ajuda a indexação).

**Surfacing no catálogo** (descoberta interna → ajuda o Google a achar a página):

- `site/src/pages/index.astro`: nova seção "Em breve" no fim, mapeando
  `loadComingSoon()` num `ComingSoonCard` (card discreto, sem valor/métricas).
  **Não** entrar na tabela "Resumo dos indicadores" (que depende de `latest`).
- `site/src/pages/[category]/index.astro`: carregar `loadComingSoon()`, filtrar
  por categoria e renderizar uma seção "Em breve" abaixo dos ativos.
- `ComingSoonCard.astro`: card simples (code, nome, "Em breve →") linkando
  `/{slug}/`.

## SEO (o ponto sensível)

- **URL final desde o dia 1**: `/{slug}/`. Nada de `/em-breve/...` — evita
  redirect na promoção e preserva ranking.
- **Indexável**: sem `noindex`. Incluída no sitemap automaticamente
  (`@astrojs/sitemap` cobre todas as rotas geradas). Garantir links internos
  (home + categoria) para descoberta.
- **Conteúdo genuíno**, não placeholder vazio: o bloco "o que é/para que
  serve/fonte" precisa ter substância — senão vira thin content e arrisca o
  domínio.
- **JSON-LD**: **não** emitir o schema `Dataset` enquanto não há dado (evita
  declarar `temporalCoverage`/`variableMeasured` inexistentes). Manter
  `title`/`description`/OG padrão; opcionalmente `WebPage`. O `Dataset` entra na
  promoção.
- **`title`/`description`**: focar no termo de busca do indicador + sinalizar o
  estado ("em breve"/"em construção"). Não prometer data exata.
- **`canonical`** = a própria `/{slug}/` (já é o comportamento do `BaseLayout`).

## Privacidade

O evento de interesse não coleta PII → coberto pela menção a GA4 já existente em
`site/src/pages/politica-de-privacidade.astro`. Se adicionar captura de e-mail
via formulário externo, **atualizar** essa página citando o serviço usado.

## Promoção: coming_soon → active (URL preservada)

Quando a demanda justificar, promover sem trocar a URL:

1. Pesquisa/connector pela skill `add-indicator` (passos 1–2: confirmar
   `series_id`/`tabela` e smoke do connector).
2. Migration `UPDATE indicators SET status='active', active=1,
   connector_type=..., connector_config=..., inception_date=...,
   expected_release_day=... WHERE code=...`.
3. `backfill <CODE>` → `build` → `publish`. O `/{slug}/` passa a renderizar o
   detalhe completo automaticamente (já está no `getStaticPaths`).

## Milestones / checklist

1. **M-CS1 — schema**: migration `007_indicator_status.sql`; `Indicator.status`,
   `_INDICATOR_COLUMNS`, `_row_to_indicator`, `list_coming_soon_indicators`.
   Teste: seed coming_soon não aparece em `list_active_indicators` e aparece em
   `list_coming_soon_indicators`.
2. **M-CS2 — build**: `write_coming_soon_index` + wiring no `build()` (sucesso +
   no_changes-se-faltar) + `build --force`. Testes: `coming-soon.json` gerado e
   ordenado; `no_changes` mantém `files_generated==0` quando já existe; `--force`
   reescreve.
3. **M-CS3 — site**: `loadComingSoon`, `[slug].astro` mesclado, `ComingSoon.astro`
   + `ComingSoonCard.astro`, seções "Em breve" na home e na categoria, link.
   `astro check` limpo; `astro build` gera `/{slug}/` em breve.
4. **M-CS4 — instrumentação**: CTA com evento `coming_soon_interest` (+ opcional
   `coming_soon_view`); registrar dimensões e Key Event no GA4; solicitar
   indexação no GSC.
5. **M-CS5 — conteúdo**: migrations de seed dos candidatos (IPC-Fipe, PIM-PF,
   PIB, PNAD) com descrições/fonte/SEO reais.

Smoke ao final: `bash scripts/precommit.sh` + `pytest pipeline/ -q`.

## Fora de escopo desta fase

- Backend/persistência de e-mails (sem servidor; usar formulário externo se
  necessário).
- Construir os conectores dos candidatos — só após o sinal de demanda.
- Multi-idioma das páginas "em breve" (ver seção 6 do `docs/ROADMAP.md`).
