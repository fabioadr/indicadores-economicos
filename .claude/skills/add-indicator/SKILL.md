---
name: add-indicator
description: Adiciona um novo indicador econômico ao sistema. Use quando o usuário pedir para adicionar IGP-M, SELIC, INPC, ou qualquer outro indicador novo ao catálogo.
---

# Adicionar Indicador

Workflow para adicionar um indicador novo. Não pular etapas.

## Passos

1. **Pesquisa da fonte** — invoque o subagent `bcb-research` para confirmar series_id, frequência, data de início

2. **Validação** — confirme com o usuário:
   - Code (ex: "IGPM")
   - Slug URL (ex: "igp-m")
   - Categoria (ver `docs/03-data-model.md`)
   - Frequência confirmada
   - Source URL institucional

3. **Long description** — escreva ou peça ao usuário um markdown explicando o que é o indicador (3 seções: O que é, Para que serve, Fonte). Use os existentes em `docs/08-indicators-catalog.md` como template.

4. **SEO templates** — gere meta_title e meta_description seguindo o padrão dos existentes.

5. **Migration** — crie `pipeline/db/migrations/NNN_add_<code>.sql` com `INSERT OR IGNORE`. Use UUID v4 fixo (gere uma vez, não muda em re-execuções).

6. **Atualizar catálogo** — adicione entrada em `docs/08-indicators-catalog.md`.

7. **Aplicar e backfill** — da raiz do repositório:

   `bash .claude/skills/add-indicator/scripts/migrate-backfill-build.sh <CODE>`

   (equivale a `migrate`, `backfill <CODE>` e `build` via CLI.)

8. **Validação final**:
   - Conta de valores no SQLite > 0
   - JSON gerado em `site/data/<slug>.json`
   - PNGs gerados em `site/public/charts/`
   - Página local renderiza: `cd site && pnpm dev`

9. **Deploy**: `python -m pipeline.cli deploy`
