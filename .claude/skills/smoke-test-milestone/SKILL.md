---
name: smoke-test-milestone
description: Executa smoke test de um milestone do plano de implementação. Use quando o usuário disser "vamos validar o milestone X" ou "smoke test do M3".
---

# Smoke Test de Milestone

1. Leia `docs/09-implementation-plan.md` na seção do milestone informado.

2. Para cada item da checklist "Entregas":
   - Verifique se está no código
   - Marque como ✅ ou ❌ no relatório

3. Execute os comandos da seção "Smoke test" do milestone.

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

## Validações específicas da Fase 3

Para milestones M17–M22, executar adicionalmente:

```bash
bash scripts/validate-fase3-build.sh
```

Por milestone:

- **M17**: validar 11 indicadores ativos, categoria atividade no ar, calculator_enabled correto
- **M18**: validar 7 calc-*.json + testes Python e Vitest passando
- **M19**: validar 7 páginas /calculadora/{slug}/ no ar, query params funcionam, fallback noscript exibe tabela
- **M20**: validar 11 sparklines em sparklines.json, dark mode adapta cor
- **M21**: validar bundle JS gzipped ≤ 50KB por página, fallback noscript funciona
- **M22**: validar comparisons.json gerado, ausência de PNGs combinatórios em /charts/comparisons/, toggle funciona