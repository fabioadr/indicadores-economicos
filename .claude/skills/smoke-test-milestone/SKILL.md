---
name: smoke-test-milestone
description: Executa smoke test de um milestone do plano de implementação de uma fase. Use quando o usuário disser "vamos validar o milestone X" ou "smoke test do M3".
---

# Smoke Test de Milestone

1. Localize o milestone no plano da fase correspondente:
   - Fase 1: `docs/fase-01/09-implementation-plan.md`
   - Fase 2: `docs/fase-02/07-implementation-plan.md`
   - Fase 3: `docs/fase-03/06-implementation-plan.md` (fase **não implementada**: tudo deve sair ❌ até ser construído)
   - Fases 4 e 5: seção de entregas em `docs/fase-0N/00-README.md`
   - Status atual das fases: `docs/PROJECT-CONTEXT.md` seção 1.

2. Para cada item da checklist "Entregas":
   - Verifique se está no código
   - Marque como ✅ ou ❌ no relatório

3. Execute os comandos da seção "Smoke test" do milestone (Python sempre via `.venv/bin/python`).
   Se o comando for `deploy`/`publish` ou outro que faça `git push`, peça confirmação antes.

4. Capture stdout e stderr de cada comando.

5. Devolva relatório estruturado:

```markdown
## Milestone N — <título>

Entregas:

- ✅ ...
- ❌ ... (motivo)

Smoke test:

- Comando: <cmd>
  Resultado: <pass/fail>
  Output: <relevant lines>

Status: PASS | PARTIAL | FAIL
Próximos passos: <se PARTIAL ou FAIL>
```

6. Não avance para o próximo milestone sem PASS.

Validação de artefatos do build (Fases 1 e 2): `bash scripts/validate-fase2-build.sh`.
