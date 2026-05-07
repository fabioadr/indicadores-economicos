---
name: add-indicator
description: Adiciona um novo indicador econômico ao sistema. Use quando o usuário pedir para adicionar IGP-M, SELIC, INPC, ou qualquer outro indicador novo ao catálogo.
---

# Adicionar Indicador

Workflow para adicionar um indicador novo. Não pular etapas. Delegue tarefas pesadas a subagents.

## Passos

0. **Decidir o conector**:
   - Indicador do BCB ou com espelho confiável no BCB SGS → `bcb_sgs` + subagent `bcb-research`
   - Indicador do IBGE que precisa de granularidade que SGS não cobre → `ibge_sidra` + subagent `sidra-research`
   - Indicador da FGV → `bcb_sgs` (espelho FGV)
   - Outras fontes → discutir com o usuário antes de implementar

1. **Pesquisa da fonte** — invoque o subagent escolhido em (0) para confirmar `series_id` (ou `tabela`/`variavel`/`localidade`), frequência, unidade, data de início, exemplo de valores recentes.

2. **Smoke do connector** — invoque o subagent `connector-smoke` com o config retornado em (1) para garantir que o fetch real funciona antes de tocar no DB.

3. **Validação com o usuário** — confirme:
   - `code` (ex: "IGPM"), `slug` (ex: "igp-m")
   - Categoria: ver `pipeline/db/migrations/004_seed_phase2_indicators.sql` para os valores existentes
   - `unit`, `frequency` (geralmente `monthly`)
   - `source_name`, `source_url` institucional

4. **Long description** — markdown com 3 seções: O que é, Para que serve, Fonte. Use os existentes em `pipeline/db/migrations/004_seed_phase2_indicators.sql` como template.

5. **SEO templates** — gere `meta_title` e `meta_description` no padrão dos existentes.

6. **Migration** — invoque o subagent `migration-author` passando todos os campos coletados nos passos 1–5. Ele numera o arquivo, gera UUID v4 fixo, escreve o SQL idempotente em `pipeline/db/migrations/NNN_add_<code>.sql`. Reveja o arquivo gerado.

7. **Aplicar e backfill** — da raiz do repositório:

   `bash .claude/skills/add-indicator/scripts/migrate-backfill-build.sh <CODE>`

   (equivale a `migrate`, `backfill <CODE>`, `build` via CLI.)

8. **Validação final** — invoque o subagent `build-validator` em background (`run_in_background=true`) para rodar:
   - `python -m pipeline.cli build` (já feito em 7, mas re-roda idempotente)
   - `bash scripts/validate-fase2-build.sh`

   Enquanto valida, confira no SQLite (MCP):
   - `SELECT COUNT(*) FROM indicator_values v JOIN indicators i ON v.indicator_id = i.id WHERE i.code = '<CODE>';` deve ser > 0
   - `site/data/<slug>.json` existe
   - `site/public/charts/<slug>-history.png` existe

9. **Render local** — `cd site && pnpm dev`, abrir `/indicadores/<slug>/`.

10. **Deploy** — `python -m pipeline.cli deploy`
