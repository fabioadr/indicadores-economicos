---
name: release-check
description: Smoke check obrigatório antes de commit ou push de mudanças no pipeline ou site. Use quando o usuário pedir "checa antes de subir", "valida antes de commitar", ou explicitamente "/release-check".
---

# Release Check

Workflow para validar mudanças antes de commit/push, sem inflar o contexto principal.

## Etapas

Rodar as 4 primeiras etapas em paralelo onde possível. Capturar exit codes; mostrar só o sumário consolidado.

1. **Lint Python**: `.venv/bin/ruff check pipeline/`
   - PASS se exit 0
   - FAIL: primeira linha de cada erro

2. **Testes Python**: `.venv/bin/pytest pipeline/ -q --no-header --tb=line`
   - Rodar com `Bash(run_in_background=true)` se a árvore for grande
   - PASS se exit 0
   - FAIL: linha do primeiro teste que falhou

3. **Validate build**: `bash scripts/validate-fase2-build.sh`
   - PASS se exit 0
   - FAIL: lista de artefatos faltantes

4. **Type check site**: `cd site && pnpm astro check`
   - PASS se exit 0
   - FAIL: primeira linha de erro

5. **Git status**: `git status -s` (informativo, não falha)
   - Listar arquivos não commitados (resumido)

## Atalho

`bash scripts/precommit.sh` faz 1+3+4 em sequência fail-fast. Use isso e rode pytest separado em background se a suíte for lenta.

## Saída esperada

```
## Release check

- ruff:         PASS | FAIL | SKIP (<N> issues)
- pytest:       PASS | FAIL (<linha>)
- validate:     PASS | FAIL (<arquivo faltando>)
- astro check:  PASS | FAIL (<linha>)
- uncommitted:  <N arquivos>

Status: PASS | FAIL
```

Se FAIL em qualquer etapa, **não autorize commit/push**. Devolva primeiro erro e pergunte se o usuário quer corrigir ou seguir.

Se PASS em tudo, sugira a mensagem de commit no formato `<scope>: <descrição>` baseada no diff.
