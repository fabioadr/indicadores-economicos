# 03 — Calculadora de Correção Monetária

> Spec da feature de cabeçalho da Fase 3.

## Escopo funcional

Permite ao usuário descobrir **quanto um valor monetário equivale hoje** (ou em qualquer data passada) corrigido por um indicador de inflação ou correção monetária.

### Indicadores suportados

7 indicadores. Critério: campo `calculator_enabled = 1` no DB. Lista canônica para a Fase 3:

| Slug | Indicador | Tipo natural |
|---|---|---|
| `ipca` | IPCA | Inflação oficial |
| `ipca-15` | IPCA-15 | Inflação prévia |
| `igp-m` | IGP-M | Aluguéis (FGV) |
| `igp-di` | IGP-DI | Setor produtivo (FGV) |
| `inpc` | INPC | Inflação para renda baixa |
| `incc-m` | INCC-M | Construção civil |
| `tr` | TR | Poupança/FGTS |

### Cálculo

```
fator = ∏ (1 + valor_mensal_i / 100)
       i ∈ [data_inicial, data_final]

valor_corrigido = valor_inicial × fator
variação_total  = (fator − 1) × 100
```

### Casos de borda

- **Data inicial > data final**: trocar internamente e exibir aviso ("invertemos as datas para você")
- **Data inicial < primeiro_periodo do indicador**: bloquear, exibir mensagem clara com a data mínima disponível
- **Data final > último_periodo disponível**: usar o último período disponível e avisar (`"Cálculo até <mês> (último valor publicado)"`)
- **Mês intermediário ausente** (improvável, mas possível em séries antigas): tratar como 0% e logar warning no console (não alarmar usuário)
- **Valor inicial não-numérico, vazio ou negativo**: validação de input nativa (`type="number" min="0.01"`)
- **Valor inicial muito grande** (overflow visual): formatar com notação reduzida (`R$ 1,2 mi`) na exibição mas manter precisão no cálculo

## URL e SEO

### Estrutura

- `/calculadora/` — landing
- `/calculadora/ipca/` — calculadora IPCA
- `/calculadora/igp-m/` — calculadora IGP-M
- `/calculadora/igp-di/` — calculadora IGP-DI
- `/calculadora/inpc/` — calculadora INPC
- `/calculadora/incc-m/` — calculadora INCC-M
- `/calculadora/ipca-15/` — calculadora IPCA-15
- `/calculadora/tr/` — calculadora TR

### Templates de SEO

**Landing `/calculadora/`:**
```
<title>Calculadoras de Correção Monetária | Indicadores Econômicos Hoje</title>
<meta name="description" content="Calcule a correção monetária de qualquer valor pelos principais índices brasileiros: IPCA, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15 e TR.">
```

**Página por indicador `/calculadora/{slug}/`:**
```
<title>Calculadora {NOME} - Correção Monetária Atualizada {mês}/{ano} | Indicadores Econômicos Hoje</title>
<meta name="description" content="Calcule a correção monetária pelo {NOME} entre quaisquer datas. Dados oficiais atualizados até {mês}/{ano}, fonte {FONTE}.">
```

### JSON-LD

Cada página de calculadora adiciona um schema `WebApplication`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Calculadora IPCA",
  "applicationCategory": "FinanceApplication",
  "operatingSystem": "Web",
  "url": "https://indicadoreseconomicoshoje.com.br/calculadora/ipca/",
  "description": "..."
}
</script>
```

## UX

### Layout (mobile-first)

```
┌─────────────────────────────────┐
│ ← Indicadores                   │
│                                 │
│ Calculadora IPCA                │
│ Atualizada até abr/2026         │
│                                 │
│ ┌─────────────────────────┐     │
│ │ Valor inicial           │     │
│ │ R$ [____________]       │     │
│ │                         │     │
│ │ Data inicial            │     │
│ │ [mês ▼]  [ano ▼]        │     │
│ │                         │     │
│ │ Data final              │     │
│ │ [mês ▼]  [ano ▼]        │     │
│ │                         │     │
│ │       [Calcular]        │     │
│ └─────────────────────────┘     │
│                                 │
│ ┌─────────────────────────┐     │
│ │ R$ 1.000,00             │     │
│ │ corrigido pelo IPCA     │     │
│ │ entre jan/2020 e dez/24 │     │
│ │                         │     │
│ │ ═══════════════         │     │
│ │ R$ 1.273,45             │     │
│ │ +27,35%                 │     │
│ └─────────────────────────┘     │
│                                 │
│ Como é calculado: ...           │
│ Fonte oficial: ...              │
│                                 │
│ Tabela histórica do IPCA ↓      │
│ [tabela]                        │
└─────────────────────────────────┘
```

### Comportamento

- Cálculo é **disparado pelo botão** (não em onChange, evita ruído visual em mobile com teclado)
- Ao calcular, scroll suave até o card de resultado
- Resultado fica visível até nova interação (sem re-render se inputs idênticos)
- Botão "Compartilhar" no resultado: gera URL com query params (`?valor=1000&inicio=2020-01&fim=2024-12`) e copia para clipboard
- Carregar a página COM query params populados → cálculo é executado automaticamente
- Estado de loading: durante fetch do `calc-{slug}.json` (primeira vez), botão fica disabled com texto "Carregando dados..."

### Acessibilidade

- Inputs com `<label>` explícito
- `aria-live="polite"` no card de resultado (anuncia mudança a leitores de tela)
- Date inputs como `<select>` (mês) + `<select>` (ano), navegáveis por teclado
- Foco volta ao card de resultado após cálculo
- Contraste mínimo AA em todos os textos
- Mensagens de erro próximas ao campo, com `aria-describedby`

### Fallback sem JS

Se o usuário tiver JS desabilitado:

- Os `<select>` e o `<input>` continuam visíveis (são HTML nativo)
- O botão "Calcular" não funciona
- Abaixo dos campos, exibir aviso: "A calculadora exige JavaScript habilitado. Você pode consultar o histórico completo do {NOME} na tabela abaixo."
- A tabela histórica do indicador está sempre presente abaixo da calculadora — fallback útil

## Implementação

### Estrutura de arquivos

```
site/src/components/calculator/
├── Calculator.astro            # Container que orquestra UI + lógica
├── DateInput.astro             # Mês + ano selects
├── ResultCard.astro            # Card de resultado
├── calculator-logic.ts         # Funções puras de cálculo (testáveis)
├── calculator-ui.ts            # Bindings DOM ↔ lógica
└── calculator-types.ts         # Tipos TypeScript
```

### `calculator-logic.ts` — funções puras

```typescript
export type CalcInputs = {
  initialValue: number;      // R$
  startPeriod: string;       // 'YYYY-MM'
  endPeriod: string;         // 'YYYY-MM'
};

export type CalcResult = {
  finalValue: number;        // R$ corrigido
  variation: number;         // % total
  factor: number;            // multiplicador
  effectiveStart: string;    // pode diferir do input se foi corrigido
  effectiveEnd: string;
  warnings: string[];
};

export function calculateCorrection(
  inputs: CalcInputs,
  series: Record<string, number>,
  meta: { firstPeriod: string; lastPeriod: string }
): CalcResult {
  const warnings: string[] = [];
  
  let { initialValue, startPeriod, endPeriod } = inputs;
  
  // 1. Inverter se necessário
  if (startPeriod > endPeriod) {
    [startPeriod, endPeriod] = [endPeriod, startPeriod];
    warnings.push('As datas foram invertidas automaticamente.');
  }
  
  // 2. Bound inferior — bloqueia
  if (startPeriod < meta.firstPeriod) {
    throw new CalcError(
      `Dados disponíveis apenas a partir de ${formatPeriod(meta.firstPeriod)}.`
    );
  }
  
  // 3. Bound superior — corrige
  if (endPeriod > meta.lastPeriod) {
    endPeriod = meta.lastPeriod;
    warnings.push(`Cálculo limitado a ${formatPeriod(meta.lastPeriod)} (último valor publicado).`);
  }
  
  // 4. Validar valor
  if (!Number.isFinite(initialValue) || initialValue <= 0) {
    throw new CalcError('Informe um valor inicial maior que zero.');
  }
  
  // 5. Iterar e multiplicar
  let factor = 1;
  for (const period of periodsBetween(startPeriod, endPeriod)) {
    const v = series[period];
    if (v === undefined) {
      console.warn(`Período ${period} ausente na série; tratado como 0%.`);
      continue;
    }
    factor *= 1 + v / 100;
  }
  
  return {
    finalValue: initialValue * factor,
    variation: (factor - 1) * 100,
    factor,
    effectiveStart: startPeriod,
    effectiveEnd: endPeriod,
    warnings,
  };
}
```

### `calculator-ui.ts` — bindings

- Captura DOM no DOMContentLoaded
- Liga handlers nos selects + botão
- Lê query params na inicialização e dispara cálculo se válidos
- Atualiza URL com `history.replaceState` ao calcular (compartilhamento via URL)

### Carregamento dos dados (`calc-{slug}.json`)

- `<script type="module">` no Astro com `client:visible` no componente
- `fetch('/data/calc-ipca.json')` — Vercel já serve gzip
- Cache no `sessionStorage` (vida útil = sessão; evita refetch em navegação interna)
- Promise compartilhada se múltiplos handlers chamarem antes do primeiro completar

### Testes (M19)

Em `pipeline/tests/test_calculator_data.py`:

- Para 5 casos conhecidos (R$ 1.000 IPCA jan/2020 → dez/2024, etc.), valida que o `calc-{slug}.json` produz o resultado esperado
- Casos de referência podem vir do **Calculadora do Cidadão (BCB)** ou do BC mesmo

Em `site/src/components/calculator/__tests__/calculator-logic.test.ts` (Vitest):

- Mesmos casos validados client-side
- Casos de borda: data invertida, data fora de bound, valor inválido, mês ausente

## Conteúdo educacional na página

Cada página de calculadora deve ter, abaixo do card:

- **"Como é calculado"** (parágrafo curto, fórmula em linguagem natural)
- **"Quando usar este índice"** (3–4 itens curtos, ex: "Aluguel residencial: IGP-M")
- **"Fonte oficial"** (link para BCB / FGV / IBGE)
- **Disclaimer**: "Os cálculos são informativos. Para fins jurídicos ou contratuais, consulte fonte oficial."

> Conteúdo escrito por humano (Fábio); o seed inicial pode ser drafted pelo Claude Code mas requer revisão antes do deploy.

## Compartilhamento (Open Graph)

Cada página tem OG image dedicada gerada em build:

- 1200x630 PNG
- Texto: "Calculadora {NOME}" + último valor + data
- Mesmo template da OG image do indicador, com sufixo "Calculadora" no header
