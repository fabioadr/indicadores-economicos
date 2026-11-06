---
name: add-indicator
description: Adiciona um novo indicador econômico ao sistema. Use quando o usuário pedir para adicionar um indicador novo ao catálogo (ex. PIB, IPC-Fipe, uma série nova do BCB ou do IBGE).
---

# Adicionar Indicador

Workflow para adicionar um indicador novo. Não pular etapas. Delegue tarefas pesadas a subagents.

## Passos

0. **Decidir o conector**:
   - Indicador do BCB ou com espelho confiável no BCB SGS → `bcb_sgs` + subagent `bcb-research`
   - Indicador do IBGE que precisa de granularidade que SGS não cobre → `ibge_sidra` + subagent `sidra-research`
   - Indicador da FGV → `bcb_sgs` (espelho FGV)
   - Outras fontes → discutir com o usuário antes de implementar (conector novo = plugin em `pipeline/connectors/`)

1. **Pesquisa da fonte** — invoque o subagent escolhido em (0) para confirmar `series_id` (ou `tabela`/`variavel`/`localidade`), frequência, unidade, data de início, exemplo de valores recentes.

2. **Smoke do connector** — invoque o subagent `connector-smoke` com o config retornado em (1) para garantir que o fetch real funciona antes de tocar no DB.

3. **Validação com o usuário** — confirme:
   - `code` (ex: "IGPM"), `slug` (ex: "igp-m"; vira a URL `/<slug>/`)
   - Categoria e unidade: use as existentes (`SELECT DISTINCT category, unit FROM indicators;`).
     **Categoria nova** exige mexer no site e no build: procure uma categoria existente (ex. `trabalho`) em
     `pipeline/core/builder.py`, `pipeline/core/charts.py`, `site/src/lib/data.ts` (`CategoryKey`),
     `site/src/lib/format.ts`, `site/src/components/ui/CategoryPill.astro`, `site/src/pages/index.astro` e
     `site/src/pages/[category]/index.astro`.
   - `aggregation_mode`: `compound_monthly` (variação % mensal), `compound_daily_to_monthly` (série diária),
     `none` (taxa anualizada, não compõe) ou `level` (saldo/fluxo/índice). Ver `pipeline/core/aggregations.py`.
   - `frequency` (geralmente `monthly`), `source_name`, `source_url` institucional, `expected_release_day`.

4. **Long description** — markdown com 3 seções: O que é, Para que serve, Fonte. Use como template as migrations mais recentes de indicador (`008_add_poupanca_imobiliario.sql`, `009_add_salmin.sql`).

5. **SEO templates** — gere `meta_title` e `meta_description` no padrão dos existentes (ver `007_seo_meta_revision.sql` e `docs/SEO.md`).

6. **Migration** — invoque o subagent `migration-author` passando todos os campos coletados nos passos 1–5. Ele numera o arquivo, gera UUID v4 fixo, escreve o SQL idempotente em `pipeline/db/migrations/NNN_add_<code>.sql`. Reveja o arquivo gerado.

7. **Aplicar e backfill** — da raiz do repositório:

   `bash .claude/skills/add-indicator/scripts/migrate-backfill-build.sh <CODE>`

   (equivale a `migrate`, `backfill <CODE>`, `build` via CLI.)

8. **Validação final** — invoque o subagent `build-validator` em background para rodar o build e
   `bash scripts/validate-fase2-build.sh`. Enquanto valida, confira:
   - `SELECT COUNT(*) FROM indicator_values v JOIN indicators i ON v.indicator_id = i.id WHERE i.code = '<CODE>';` deve ser > 0 (SQLite MCP)
   - `site/data/<slug>.json` existe
   - `site/public/charts/<slug>-history.png` existe
   - Se o indicador deve entrar nas validações permanentes, adicione o slug em `scripts/validate-fase2-build.sh`.

9. **Render local** — `cd site && pnpm dev`, abrir `http://localhost:4321/<slug>/`.

10. **Deploy** — só com pedido explícito: `.venv/bin/python -m pipeline.cli deploy` (git push → Vercel).
