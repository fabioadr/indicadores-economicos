# SEO — Indicadores Econômicos Hoje

Documento **vivo** de conhecimento de SEO. Diz, de forma opinativa, **o que traz tráfego
de valor para este site e o que é ruído** — para guiar decisões de título, conteúdo e
priorização sem reaprender a cada análise.

Não confundir com o `ROADMAP.md` (backlog de features) nem com `CLAUDE-DETAILS.md`
(diretrizes de engenharia). Aqui é a **tese de busca**: por que ranqueamos, para quê vale
a pena ranquear, e onde mexer no código quando for executar. Toda afirmação abaixo está
ancorada nos dados de Search Console (GSC) e GA4 em `docs/gsc/` e `docs/ga/` (snapshot
YTD 2026).

## Tese de SEO — por que ranqueamos

O site ganha busca por um motivo só: **dado oficial, autêntico, auto-atualizado e fresco**,
exposto com UX melhor do que a fonte. As fontes (BCB, IBGE, FGV) têm o número, mas não
entregam "o CDI de hoje em uma tabela limpa com histórico". Nós entregamos.

Disso decorre tudo:

- **Frescor é o ativo.** Título e meta carregam o valor e o mês/ano correntes via template
  (`{value}`, `{month_name}`, `{year}`). Cada coleta renova o snippet sem reescrever nada.
  Concorrente estático com número velho perde para nós.
- **O volume está na long-tail indicador × período.** "cdi abril 2026", "igpm janeiro
  2026", "taxa referencial tr maio 2026 valor" — milhares de variações que a tabela
  histórica cobre naturalmente. Não se persegue uma a uma; cobre-se com estrutura.
- **Nosso nicho é o número + a tabela + o histórico.** Não disputamos análise editorial
  nem notícia. Disputamos "qual o valor e onde vejo a série".

## Famílias de consulta — o que vale ouro e o que é ruído

Classificação baseada nas consultas reais do GSC (`docs/gsc/Consultas.csv`). "Posição" é a
média no GSC; quanto menor, melhor.

| Família | Exemplo real (impressões / posição) | Valor | Ação |
|---|---|---|---|
| `X hoje` / `valor de X hoje` | `cdi hoje` (59 / **70**), `inflação hoje` (33 / 49), `ipca hoje` (15 / 46), `inpc hoje` (25 / 39) | **OURO** | Alto volume e **posição péssima** — a maior lacuna do site. O número existe na página; falta o termo "hoje" + valor no título/H1. |
| `X {mês}/{ano}` | `cdi abril 2026` (pos ~9), `taxa referencial tr abril 2026 valor` (89 / **8.4**), `tabela de igpm 2026` (25 / 8.2) | **ALTO — já converte** | Padrão datado **já ranqueia na página 1**. **Preservar.** Não sacrificar ao otimizar para "hoje". |
| `taxa X atual` / `valor X` | `taxa tr atual brasil 2026` (33 / 9), `valor do cdi` (17 / 71) | ALTO | Mesma intenção transacional de "hoje". Cobrir junto. |
| `X acumulado` / `X 12 meses` | `cdi acumulado 12 meses abril 2026` (12 / 9), `selic acumulada` (20 / 60) | ALTO | A hero já mostra acumulado no ano / 12m / 24m. Garantir que o termo apareça em texto indexável. |
| `tabela X` / `histórico X` | `tabela de igpm 2026` (25 / 8.2), `incc ultimos 10 anos` (83 / **7.2**) | ALTO | Casa direto com nossas tabelas anual e histórica. Forte candidato a página 1. |
| `X {ano histórico}` | `igpm 2020`, `cdi 2021`, `selic 2017` | MÉDIO | Capturado pela tabela histórica. Não exige ação dedicada. |
| Long-tail com dado embutido | `cdi abril 2026 14,65`, `taxa di cetip 28/05/2026 14,40` | BOM — automático | Capturado sem esforço pelo frescor do snippet. Não otimizar manualmente. |
| Paths de imagem `.png` | `/igp-m/grafico-...-2020-...png` (1–3 impr) | IGNORAR | Ruído de indexação de assets. Sem ação. |
| Marca pura | `indicadores econômicos hoje` (110 / 13) | Baixo esforço | Já nosso por definição; não investir. |

**Regra de ouro:** otimização vale a pena onde **há volume E a posição é ruim E temos o
dado**. As três coisas juntas. `X hoje` é o caso perfeito. `cdi abril 2026` já está bom —
não mexer só para mexer.

## Sinais a ignorar na análise (ruído)

Para não tirar conclusão errada dos relatórios:

- **Referral spam / falsos buscadores.** Em `docs/ga/aquisicao-...csv` aparecem dezenas de
  origens como `yometa.com`, `blekko.com`, `teoma.com`, `geona.com`, `panjoy.com`,
  `multisearching.com`. São spam/bots de referral, **não** usuários. Ignorar na leitura de
  aquisição; olhar Organic Search, Direct e os buscadores reais (Google, Bing, Yahoo,
  DuckDuckGo, ChatGPT/Copilot).
- **Duplicidade www vs apex e `/index.html` legado.** O GSC lista tanto
  `https://indicadoreseconomicoshoje.com.br/...` quanto
  `https://www.indicadoreseconomicoshoje.com.br/...index.html` recebendo impressões. São
  URLs antigas indexadas competindo com as canônicas (`/{slug}/`). Diluem autoridade — ver
  "Mudanças recomendadas".
- **CTR=0% em posição alta não é falha de conteúdo.** `/tr/` tem 2.318 impressões e 0
  cliques na posição ~12 (fundo da página 1 / topo da 2). É problema de **posição +
  snippet**, não de dado faltando.

## Anomalia conhecida — Bing > Google

No snapshot YTD 2026, **Bing (216 sessões) supera o Google (44)** como buscador de origem,
com Yahoo (54, que usa índice Bing) em segundo. Isso é atípico: o normal é Google dominar.
Leitura: o conteúdo é bom (o Bing valida), mas o **Google ainda subavalia o domínio** —
autoridade jovem e/ou as URLs duplicadas acima. Não é problema de conteúdo a resolver
página a página; é maturação de domínio + higiene de URL. Monitorar, não entrar em pânico.

## Alavancas on-page e onde vivem no código

Onde mexer quando for executar. Mapa alavanca → arquivo:

| Alavanca | Arquivo | Observação |
|---|---|---|
| Título + meta description (por indicador) | seeds `pipeline/db/migrations/002_*`, `004_*`, `005_*` | Templates com `{month_name}/{year}/{value}/{last_12m}`. Mudança = nova migration idempotente com `UPDATE`. |
| Interpolação dos templates | `site/src/pages/[slug].astro` (`fillMeta`, ~linha 36) | **Cuidado:** `String.replace(string)` troca só a 1ª ocorrência. Templates que reusam um token precisam de replace global. |
| H1 e bloco de valor | `site/src/components/domain/IndicatorHero.astro` | H1 = `indicator.name` (sem "hoje"/valor hoje). Valor/acumulados aparecem no card, não no H1. |
| JSON-LD (Dataset) | `[slug].astro`, `comparar/[slug].astro` | Schema `Dataset`. Espaço para enriquecer intenção "hoje" (ex.: valor corrente). |
| Canonical / OG / Twitter | `site/src/layouts/BaseLayout.astro` | Canonical = `Astro.url.pathname` sobre `astro.config.mjs#site` (apex). |
| Categorias | `site/src/pages/[category]/index.astro` | Título/descrição por categoria, hardcoded. |
| Comparações | `pipeline/config_groups.py` + `comparar/[slug].astro` | Grupos curados com título/descrição próprios. |
| Sitemap / robots | `@astrojs/sitemap` (auto) + `site/public/robots.txt` | Sitemap gerado no build; cobre rotas dinâmicas. |

## Padrões de título e meta (regras)

Estado atual (todos os indicadores seguem o mesmo molde):

```
IPCA - Tabela atualizada {month_name}/{year} | Indicadores Econômicos Hoje
IPCA de {month_name}/{year}: {value}%. Acumulado 12 meses: {last_12m}%. Tabela histórica completa desde 1980.
```

Problema: o título **não contém "hoje"** (só na marca, no fim) nem o valor — por isso não
compete por `cdi hoje` / `ipca hoje`, a família OURO.

**Fórmula de título recomendada** (decisão registrada):

```
{CODE} hoje: {value}% em {month_name}/{year} — tabela e histórico | Indicadores Econômicos Hoje
→ CDI hoje: 14,65% em maio/2026 — tabela e histórico | Indicadores Econômicos Hoje
```

Regras:

- **Ordem:** termo-alvo (`{CODE} hoje`) → valor → data → qualificador (`tabela e
  histórico`) → marca no fim. O mais valioso primeiro; a marca por último.
- Capturar **"hoje" sem perder o datado**: ambos os padrões (`X hoje` e `X {mês}/{ano}`)
  cabem no mesmo título. Nunca remover o `{month_name}/{year}` — ele já converte.
- **Comprimento:** mirar ≤ ~60 caracteres antes do `|` marca, para não truncar na SERP.
- **Valor no snippet sempre** — é o diferencial de frescor. Já é assim na meta; levar
  também ao título.
- Ao reescrever títulos que **já ranqueiam** (datado), medir antes/depois no GSC. Mudança
  de título pode oscilar ranking por algumas semanas.

## Anti-padrões — Coisas a NÃO fazer em SEO

- ❌ **Thin content / "em breve" vazio.** Página sem dado útil de verdade vira thin content
  e arrasta o domínio. Páginas "coming soon" só com conteúdo genuíno (ver
  `docs/fase-05/00-README.md`).
- ❌ **Keyword stuffing.** Repetir "cdi hoje cdi atual cdi valor hoje" em título/H1. Um
  termo-alvo claro por página.
- ❌ **Trocar o slug de uma página que ranqueia** sem redirect 301. Slug é permanente
  (`/{slug}/` desde o dia 1). URL que ranqueia é patrimônio.
- ❌ **Deixar www vs apex e `/index.html` competirem** sem canonical/redirect.
- ❌ **Reescrever em massa títulos que já convertem** (família datada) sem medir. Otimizar
  onde dói (família "hoje"), não onde já funciona.
- ❌ **Perseguir consulta sem dado nosso por trás.** Não inventar página para um termo que
  não temos como responder com número oficial.

## Métrica e cadência

- **Fontes:** dumps em `docs/gsc/` (Consultas, Páginas) e `docs/ga/` (aquisição, páginas,
  eventos). Reexportar a cada revisão; ver guia de exportação no histórico de chat / GA4
  Query Explorer.
- **O que olhar primeiro:** **impressões × posição = oportunidade.** Muita impressão +
  posição ruim (15–70) = alvo. Posição boa + CTR baixo = problema de snippet/título.
- **Não confiar em CTR isolado** em posição alta (ver `/tr/`).
- **Cadência:** revisão trimestral, ou após qualquer mudança grande de título/estrutura
  (comparar GSC antes/depois). Ignorar ruído de referral spam na leitura de aquisição.

## Estado atual e oportunidades (snapshot jun/2026)

Crescendo: semana 22 bateu **111 usuários ativos** (recorde; máximo de 19 em 2H2025);
Organic Search virou o maior canal (247 novos usuários). Quase 100% são novos visitantes
(434 `first_visit` de 433 usuários) — retenção baixa, esperado para conteúdo de consulta.

Oportunidades priorizadas (viram a seção abaixo):

1. **Família "X hoje"** — maior lacuna. `cdi hoje` pos ~70, `ipca hoje` ~46, `inflação
   hoje` ~49. Temos o dado; falta o termo no título/H1.
2. **`/cdi/`** — **4.062 impressões** (a maior do site), posição ~23, CTR 0,17%. Subir de
   posição multiplica tráfego.
3. **`/tr/`** — 2.318 impressões, **0 cliques**, posição ~12. Snippet/posição na fronteira
   da página 1.
4. **`/selic-acumulada/`** — 717 impressões, posição ~12; consultas próximas da página 1.
5. **URLs duplicadas** (www / `/index.html`) diluindo autoridade.

## Mudanças recomendadas (âncora para execução)

Documentadas aqui; execução em rodada própria (cada uma com `/release-check`).

1. **Revisão de título/meta** — nova migration idempotente `007_seo_meta_revision.sql`
   (`UPDATE indicators SET meta_title, meta_description`) aplicando a fórmula
   `{CODE} hoje: {value}% em {month_name}/{year} — tabela e histórico | …`. Maior alavanca;
   beneficia `/cdi/` e `/tr/` sem tocar no build. Medir no GSC antes/depois.
2. **`fillMeta` global** (`site/src/pages/[slug].astro`) — trocar `String.replace` por
   replace global, para o título poder reusar tokens com segurança.
3. **H1 / lead** (`IndicatorHero.astro`) — levar `{CODE} hoje` + valor para texto
   indexável no topo (H1 ou parágrafo-líder), sem keyword stuffing.
4. **Linkagem interna** — reforçar links para `/cdi/`, `/tr/`, `/selic-acumulada/` a partir
   da home e das categorias, para empurrar a posição de páginas que já ranqueiam.
5. **Higiene de URL (opcional, alto valor)** — auditar e resolver www vs apex e
   `/index.html` legado via canonical/redirect 301, para concentrar autoridade nas
   canônicas `/{slug}/`.
