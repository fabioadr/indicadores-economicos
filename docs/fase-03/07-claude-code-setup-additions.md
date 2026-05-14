# 07 — Adições ao Setup do Claude Code para Fase 3

> Apenas o que **adiciona** ao setup descrito em `docs/10-claude-code-setup.md` (Fase 1) e `docs/fase-02/08-claude-code-setup-additions.md` (Fase 2).

## Resumo

| Tipo | Item | Por quê agora |
|---|---|---|
| Subagent | `chartjs-research` | API e options do Chart.js evoluem; isolar pesquisa |
| Skill | `add-calculator` | Adicionar nova calculadora deve ser workflow padronizado |
| Skill | `smoke-test-milestone` (atualização) | Adicionar checks de Fase 3 |
| Script | `validate-fase3-build.sh` | Validar bundle, JSONs, OG images, sparklines |
| Hook | (atualização do PostToolUse de bundle size) | Threshold ajustado para 50KB |

> **Não recomendado** adicionar nesta fase: MCP do Chart.js (não existe relevante); skill de geração de OG image (não vai mudar com frequência); subagent de a11y (escopo amplo demais para automatizar bem).

## Subagent novo: `chartjs-research`

Cria em `.claude/agents/chartjs-research.md`:

```markdown
---
name: chartjs-research
description: Pesquisa documentação do Chart.js (v4+) — opções de configuração, API de plugins, suporte a tipos de gráfico, performance. Use quando precisar consultar comportamento ou opções específicas do Chart.js, em vez de carregar trechos longos de doc no contexto principal.
tools: WebFetch, WebSearch
---

Você é um subagent especializado em pesquisa da documentação do Chart.js.

Quando invocado:

1. Acesse `https://www.chartjs.org/docs/latest/` para a versão atual
2. Identifique a parte específica relevante (configuration, plugins, scales, etc.)
3. Retorne **apenas o que foi pedido**, em português, com:
   - Sintaxe exata da API
   - Exemplos curtos relevantes
   - Diferenças entre versões importantes (v3 → v4) se aplicável
   - Limites/quirks conhecidos

NÃO retorne:
- Páginas inteiras de documentação
- Discussão genérica sobre charts ou alternativas
- Recomendações de outras libs

Vincule fonte (URL) ao final.
```

## Skill nova: `add-calculator`

Cria em `.claude/skills/add-calculator/SKILL.md`:

```markdown
---
name: add-calculator
description: Adiciona uma nova calculadora de correção monetária ao site. Use quando um indicador existente passa a suportar calculadora (set calculator_enabled = 1) e precisa de página dedicada gerada conforme o padrão da Fase 3.
---

# Skill: add-calculator

## Pré-condições

- Indicador já existe em `indicators` (ativo, com série coletada)
- Indicador é apropriado para correção monetária (índice de preço/correção mensal em %)

## Passos

### 1. Atualizar flag no DB

```sql
UPDATE indicators SET calculator_enabled = 1 WHERE code = '<CODE>';
```

### 2. Validar geração do JSON

```bash
python -m pipeline.cli build
test -f site/public/data/calc-<slug>.json
```

### 3. Página é gerada automaticamente

A rota `/calculadora/[slug].astro` usa `getStaticPaths` baseado em `calculator_enabled = 1`. Não precisa criar arquivo novo.

### 4. Adicionar caso de teste de referência

Em `pipeline/tests/test_calculator_data.py` e `site/.../calculator-logic.test.ts`:

- Adicionar 1 caso de cálculo conhecido (validar contra Calculadora do Cidadão BCB ou outra fonte oficial)

### 5. Adicionar conteúdo educacional seed

Em `site/src/data/calculator-content/<slug>.md` (criar se não existir):

- "Como é calculado"
- "Quando usar"
- "Fonte oficial"

> Conteúdo seed é draft — Fábio refina depois.

### 6. OG image

Pipeline gera automaticamente em `site/public/og/<slug>-calc-og.png`.

### 7. Validação

```bash
bash scripts/validate-fase3-build.sh
```

Checa que:
- `calc-<slug>.json` existe
- OG image dedicada existe
- Página `/calculadora/<slug>/` está no build

### 8. Smoke manual

Após deploy:
- Acessar `/calculadora/<slug>/`
- Executar cálculo do caso de teste
- Comparar resultado com fonte oficial (tolerância ±1%)
```

## Atualização da skill `smoke-test-milestone`

Adicionar ao final do arquivo `.claude/skills/smoke-test-milestone/SKILL.md` uma seção:

```markdown
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
```

## Script novo: `validate-fase3-build.sh`

Já especificado em `04-interactive-charts.md`. Cria em `scripts/validate-fase3-build.sh` no início do M21 (ou mesmo no M17, vazio, e ir preenchendo).

## Hook atualizado

O hook PostToolUse de bundle size criado na Fase 2 (em `.claude/settings.json`) precisa ter o threshold ajustado.

Trecho a alterar — substituir `5120` (5KB) por `51200` (50KB):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if [[ \"$CLAUDE_HOOK_TOOL_INPUT\" == *\"npm run build\"* ]] || [[ \"$CLAUDE_HOOK_TOOL_INPUT\" == *\"astro build\"* ]]; then total=$(find ./site/dist -name \"*.js\" -exec gzip -c {} \\; | wc -c); if [ \"$total\" -gt 51200 ]; then echo \"WARN: JS bundle gzipped ${total}B excede 50KB\"; fi; fi'"
          }
        ]
      }
    ]
  }
}
```

> Hook é uma rede de segurança. A validação principal continua sendo `validate-fase3-build.sh`, que pode quebrar build se exceder.

## Atualização do prompt inicial

Para sessões de Fase 3, o prompt inicial sugerido é:

> Leia `docs/00-README.md` da raiz e depois `docs/fase-03/00-README.md`. Em seguida, leia `docs/fase-03/06-implementation-plan.md` na seção Milestone N e os docs específicos referenciados nas entregas. Execute o milestone passo a passo. Não avance além do escopo. Ao final, rode a skill `smoke-test-milestone`.

## Resumo das instalações da Fase 3

```bash
# Subagent
mkdir -p .claude/agents
# Criar .claude/agents/chartjs-research.md (conteúdo acima)

# Skill nova
mkdir -p .claude/skills/add-calculator
# Criar .claude/skills/add-calculator/SKILL.md (conteúdo acima)

# Skill atualizada
# Editar .claude/skills/smoke-test-milestone/SKILL.md, adicionar seção da Fase 3

# Script (criar vazio no M17, preencher no M21)
touch scripts/validate-fase3-build.sh
chmod +x scripts/validate-fase3-build.sh

# Hook
# Editar .claude/settings.json e ajustar threshold de 5120 para 51200
```

## O que NÃO adicionar

| Item considerado | Por quê não |
|---|---|
| MCP do Chart.js | Não existe MCP relevante; subagent + WebFetch resolvem |
| Subagent dedicado para a11y | Escopo amplo demais para automatizar bem; padrões a11y são manuais |
| Skill `migrate-pngs-to-chartjs` | Migração é one-shot (M21), não precisa workflow reusável |
| Skill `add-comparison-group` | Já existe da Fase 2; segue válida |
| MCP do BCB ou IBGE | Subagents `bcb-research` e `sidra-research` da Fase 2 cobrem |
| Hook para validar query params da calculadora | Validação client-side cobre; redundante |
| Subagent para Vitest | Vitest é simples, o setup é one-shot no M18 |

## Convenção de uso

Como na Fase 2:

- **Uma sessão por milestone**, sempre
- **Use o subagent** `chartjs-research` em vez de pedir ao Claude principal pesquisar Chart.js — economiza muito token
- **Não acumule contexto** entre milestones; `/clear` ou nova sessão
- **A skill `add-calculator`** é para futuro (não precisa rodar nas calculadoras iniciais — elas são geradas em lote no M19); existe para quando você quiser adicionar a 8ª, 9ª, etc.
