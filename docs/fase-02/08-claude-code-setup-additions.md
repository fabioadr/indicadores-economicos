# 08 — Adições ao Setup do Claude Code para Fase 2

> Este documento lista **apenas o que adiciona** ao setup descrito em `docs/10-claude-code-setup.md` da Fase 1. Tudo que está no setup da Fase 1 permanece.

## TL;DR

**Adicionar:**
- 1 subagent novo: `sidra-research`
- 1 skill nova: `add-comparison-group`
- 2 scripts novos: `validate-fase2-build.sh`, `regenerate-comparisons.sh`
- 1 hook novo: PostToolUse para verificar bundle JS

**Ajustar:**
- Skill `add-indicator` da Fase 1 ganha decisão "BCB ou SIDRA"
- Skill `smoke-test-milestone` continua válida (referencia novos milestones)

**Remover:** nada.

---

## Subagent novo: `sidra-research`

`.claude/agents/sidra-research.md`:

```markdown
---
name: sidra-research
description: Pesquisa tabelas e variáveis no SIDRA/IBGE. Use quando precisar mapear um indicador IBGE a um connector_config (tabela + variavel + localidade), ou validar que uma combinação está correta e ativa.
tools: WebFetch, WebSearch
---

Você é especialista no SIDRA — Sistema IBGE de Recuperação Automática.

Quando recebe o nome de um indicador IBGE (ex: "IPCA-15", "INPC", "PNAD Contínua"):

1. Pesquise no SIDRA (https://sidra.ibge.gov.br/) qual a tabela agregada que contém o indicador
2. Identifique a variável correta (geralmente "Variação Mensal", "Variação Acumulada no Ano", "Número Índice")
3. Confirme a localidade adequada (`N1[all]` para Brasil agregado; `N7[all]` para regiões metropolitanas)
4. Valide via amostragem da API:
   GET https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos/-3/variaveis/{variavel}?localidades={localidade}

Devolva apenas:
- tabela
- variavel
- localidade recomendada
- nome oficial completo da variável (como aparece no SIDRA)
- frequência (mensal, trimestral, anual)
- data de início da série
- exemplo de 3 valores recentes

Se houver mais de uma variável candidata (ex: variação mensal vs variação no ano), liste todas com a descrição de cada e recomende qual usar para o caso de "valor mensal" do nosso modelo de dados.
```

**Por quê isolar:**
- A estrutura aninhada das respostas SIDRA é verbosa; subagent absorve e devolve só os campos relevantes
- Pesquisa em sidra.ibge.gov.br tende a trazer muito HTML; isolar evita poluir o contexto principal

---

## Skill nova: `add-comparison-group`

`.claude/skills/add-comparison-group/SKILL.md`:

```markdown
---
name: add-comparison-group
description: Adiciona um novo grupo de comparação à página /comparar/. Use quando o usuário pedir para criar uma nova visualização comparativa (ex: "compare IPCA, INPC e IGP-M num gráfico só").
---

# Adicionar Grupo de Comparação

1. **Coletar requisitos**:
   - Slug do grupo (kebab-case, sem acentos): ex `juros-vs-inflacao`
   - Título amigável: ex "Juros vs Inflação: SELIC e IPCA"
   - Descrição (1 frase): explicação para a página
   - Indicadores: lista de codes que devem ser plotados
   - Métrica: `value`, `ytd`, `last_12m` (default), `last_24m`

2. **Validar pré-requisitos**:
   - Todos os codes existem em `indicators` table?
   - Todos têm valores suficientes para a métrica? (`last_12m` requer 12+ pontos)
   - Os indicadores fazem sentido juntos? (ex: comparar IPCA com SELIC com `last_12m` é OK; comparar IPCA com TR com `value` mensal pode ser enganoso)

3. **Adicionar no código**:
   - Editar `pipeline/config/indicator_groups.py`
   - Adicionar dict no array `INDICATOR_GROUPS`

4. **Regenerar build**:
   ```bash
   python -m pipeline.cli build
   ```
   Ou executar `bash scripts/regenerate-comparisons.sh` se existir.

5. **Validar**:
   - PNG gerado em `site/public/charts/compare-{slug}.png`
   - Entrada em `site/data/groups.json`
   - Local dev render em `/comparar/{slug}/`

6. **Deploy**:
   ```bash
   python -m pipeline.cli deploy
   ```
```

---

## Skill ajustada: `add-indicator` (atualização da Fase 1)

A skill `add-indicator` da Fase 1 ganha um passo extra antes do passo "Pesquisa da fonte":

```markdown
1. **Decidir o conector**:
   - Se o indicador é do BCB ou tem espelho confiável no BCB SGS → usar `bcb_sgs` e o subagent `bcb-research`
   - Se é IBGE e precisa de granularidade que SGS não tem → usar `ibge_sidra` e o subagent `sidra-research`
   - Se é FGV → usar `bcb_sgs` (espelho FGV)
   - Se é fonte sem API estável → discutir com o usuário antes de implementar
```

---

## Scripts novos

### `scripts/validate-fase2-build.sh`

Estende o `validate-build.sh` para incluir os artefatos da Fase 2.

```bash
#!/usr/bin/env bash
set -e
ERRORS=0

check() {
  if [[ -e "$1" ]]; then
    echo "✓ $1"
  else
    echo "✗ FALTANDO: $1"
    ERRORS=$((ERRORS + 1))
  fi
}

# Fase 1
check site/data/indicators.json
check site/data/ipca.json
check site/data/cdi.json
check site/data/tr.json
check site/public/charts/ipca-history.png
check site/public/charts/cdi-history.png
check site/public/charts/tr-history.png

# Fase 2: indicadores
for slug in selic igp-m igp-di inpc incc-m ipca-15; do
  check site/data/$slug.json
  check site/public/charts/$slug-history.png
done

# Fase 2: grupos
check site/data/groups.json
for slug in inflacao-oficial indices-fgv juros-vs-inflacao construcao-civil; do
  check site/public/charts/compare-$slug.png
done

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ $ERRORS arquivos faltando."
  exit 1
fi
echo "✓ Build da Fase 2 válido."
```

### `scripts/regenerate-comparisons.sh`

Atalho para forçar regeneração apenas dos PNGs comparativos.

```bash
#!/usr/bin/env bash
set -e
.venv/bin/python -c "
from pipeline.config.indicator_groups import INDICATOR_GROUPS
from pipeline.core.comparison_charts import generate_comparison_chart
import os

os.makedirs('site/public/charts', exist_ok=True)
for g in INDICATOR_GROUPS:
    output = f\"site/public/charts/compare-{g['slug']}.png\"
    generate_comparison_chart(g, output)
    print(f'✓ {output}')
"
```

---

## Hook novo: budget de JS

`.claude/settings.json` (adicionar no array `hooks`):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit(.*\\.(astro|ts|tsx))|Write(.*\\.(astro|ts|tsx))",
        "hooks": [
          {
            "type": "command",
            "command": "[ -d site/dist ] && find site/dist -name '*.js' -exec gzip -c {} \\; 2>/dev/null | wc -c | awk '{ if ($1 > 5120) print \"⚠️  JS bundle size: \" $1 \" bytes (>5KB budget)\" }'"
          }
        ]
      }
    ]
  }
}
```

**Função:** após qualquer edit em arquivo Astro/TS, se houver build em `dist/`, calcula o tamanho gzipped do JS e avisa se passou do budget de 5KB.

> Este hook é uma rede de segurança. Não substitui validação manual durante o desenvolvimento, mas chama atenção quando algum componente novo causa explosão de bundle.

---

## Atualização do prompt inicial de sessão

Para sessões de Fase 2, o prompt inicial sugerido é:

> Leia `docs/00-README.md` da raiz e depois `docs/fase2/00-README.md`. Em seguida, leia `docs/fase2/07-implementation-plan.md` na seção Milestone N e os docs específicos referenciados nas entregas. Execute o milestone passo a passo. Não avance além do escopo. Ao final, rode a skill `smoke-test-milestone`.

---

## Resumo das instalações da Fase 2

```bash
# Subagent
mkdir -p .claude/agents
# Criar .claude/agents/sidra-research.md (conteúdo acima)

# Skill
mkdir -p .claude/skills/add-comparison-group
# Criar .claude/skills/add-comparison-group/SKILL.md (conteúdo acima)
# Atualizar .claude/skills/add-indicator/SKILL.md com passo do conector

# Scripts
# Criar scripts/validate-fase2-build.sh e scripts/regenerate-comparisons.sh
chmod +x scripts/validate-fase2-build.sh scripts/regenerate-comparisons.sh

# Hook
# Editar .claude/settings.json e adicionar o PostToolUse de JS budget
```

---

## O que NÃO adicionar

| Item considerado | Por quê não |
|---|---|
| MCP do croniter | Sintaxe é simples; subagent ou doc fetch resolvem |
| Subagent dedicado para charts comparativos | matplotlib é bem documentado; não precisa de isolamento |
| Skill para "adicionar Astro Island" | Componentes únicos não justificam workflow reusável |
| Skill `migrate-to-sidra` | Não vai acontecer na Fase 2; revisitar na Fase 3 se houver |
| Hook para regenerar comparisons em cada build | O builder já faz isso; redundante |
