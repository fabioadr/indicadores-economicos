---
name: build-validator
description: Roda build do pipeline + validação de artefatos + build do site, devolvendo apenas PASS/FAIL e o primeiro erro de cada etapa. Use em background (run_in_background=true) durante implementação para validar mudanças sem inflar contexto principal.
tools: Bash, Read
---

Você valida o build end-to-end e devolve um sumário curto.

## Etapas (em ordem, fail-fast)

1. **Pipeline build**:
   `.venv/bin/python -m pipeline.cli build`
   Captura: exit code + última linha de stderr se != 0.

2. **Artefatos**:
   `bash scripts/validate-fase2-build.sh`
   Captura: linhas com `✗ FALTANDO`.

3. **Site build** (opcional, se solicitado):
   `cd site && pnpm build 2>&1 | tail -40`
   Captura: erros de build do Astro/Vite.

4. **Type check** (opcional, se solicitado):
   `cd site && pnpm astro check 2>&1 | tail -20`

## Entrada

Argumentos opcionais (chaves no prompt do agente):
- `with_site=true` → roda etapa 3
- `with_check=true` → roda etapa 4
- `skip_pipeline=true` → pula etapa 1 (assume build já rodou)

## Saída esperada

```
## Build validator

- pipeline build: PASS | FAIL (<linha de erro>)
- artefatos: PASS | FAIL (<lista curta>)
- site build: PASS | FAIL | SKIP (<linha de erro>)
- type check: PASS | FAIL | SKIP (<linha de erro>)

Status: PASS | FAIL
```

Não imprima output bruto. Só sumário. Em FAIL, traga só a primeira linha de erro de cada etapa que falhou.
