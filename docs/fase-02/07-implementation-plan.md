# 07 — Plano de Implementação Fase 2

Sequência de milestones a partir de M10 (continuando da Fase 1, que vai até M9).

## Princípios (recap da Fase 1)

- Cada milestone produz algo testável de ponta a ponta
- Não pular para o próximo se o atual não estiver verde
- Smoke test manual ao final
- Branch por milestone se quiser reverter sem complicação

---

## Milestone 10 — Migration + seeds da Fase 2

**Objetivo:** estrutura no banco para Fase 2 sem ainda integrar nada.

**Entregas:**

- [✅] Migration `003_schedule_overrides.sql` com a tabela e seed da configuração padrão
- [✅] Migration `004_seed_phase2_indicators.sql` com SELIC, IGP-M, IGP-DI, INPC, INCC-M, IPCA-15
- [✅] Atualização do `08-indicators-catalog.md` da raiz com os 6 novos indicadores (mover/copiar de `fase2/04-indicators-catalog.md` para o catálogo principal)
- [✅] UUIDs v4 reais (não os placeholders) gerados e fixados nas seeds
- [✅] Long descriptions completas no SQL (markdown escapado)
- [✅] `pipeline.cli migrate` aplicada com sucesso

**Não implementar nesta milestone:**

- Conector IBGE SIDRA (próximo milestone)
- Coletas dos novos indicadores

**Smoke test:**

```bash
python -m pipeline.cli migrate
sqlite3 data/indicadores.db "SELECT code, slug, category, connector_type FROM indicators;"
# Esperado:
# IPCA       | ipca       | inflacao            | bcb_sgs      (Fase 1)
# CDI        | cdi        | juros               | bcb_sgs      (Fase 1)
# TR         | tr         | correcao_monetaria  | bcb_sgs      (Fase 1)
# SELIC      | selic      | juros               | bcb_sgs
# IGPM       | igp-m      | inflacao            | bcb_sgs
# IGPDI      | igp-di     | inflacao            | bcb_sgs
# INPC       | inpc       | inflacao            | bcb_sgs
# INCCM      | incc-m     | construcao_civil    | bcb_sgs
# IPCA15     | ipca-15    | inflacao            | ibge_sidra

sqlite3 data/indicadores.db "SELECT cron_expression, enabled FROM schedule_overrides;"
# Esperado: 0 7 * * * | 1
```

> Antes de gerar a migration, use o subagent `bcb-research` para validar os 5 series_id do BCB.

---

## Milestone 11 — Conector IBGE SIDRA

**Objetivo:** segundo conector funcionando, sem ainda coletar nada em produção.

**Entregas:**

- [✅] `pipeline/connectors/ibge_sidra.py` com `IBGESIDRAConnector` registrado como `ibge_sidra`
- [✅] Suporte a paginação por janelas (60 períodos por chamada)
- [✅] Tratamento de `"-"`, `"..."` e ausentes
- [✅] Tratamento de múltiplas localidades (filtro pela configurada)
- [✅] Testes em `pipeline/connectors/tests/test_ibge_sidra.py` cobrindo:
  - [✅] Janela única com resposta válida
  - [✅] Múltiplas janelas (paginação)
  - [✅] Períodos faltantes (`"-"`)
  - [✅] HTTP 404
  - [✅] JSON malformado
  - [✅] Período não-mensal (rejeitar)
- [✅] Fixtures em `tests/fixtures/sidra/` com respostas reais capturadas uma vez

**Correção lateral aplicada no M11:** seed M10 do IPCA-15 estava com `tabela=7060` (HTTP 500). Corrigido para `tabela=3065` em [pipeline/db/migrations/004_seed_phase2_indicators.sql](../../pipeline/db/migrations/004_seed_phase2_indicators.sql) e via `UPDATE` no `data/indicadores.db`.

**Smoke test:**

```bash
python -c "
from datetime import date
from pipeline.connectors.ibge_sidra import IBGESIDRAConnector
points = IBGESIDRAConnector().fetch(
    {'tabela': 3065, 'variavel': 355, 'localidade': 'N1[all]'},
    since=date(2024, 1, 1),
)
print(f'{len(points)} pontos coletados')
for p in points[:3]:
    print(p)
"
```

---

## Milestone 12 — Backfill e build dos novos indicadores

**Objetivo:** os 6 novos indicadores na home com séries históricas completas.

**Entregas:**

- [✅] Backfill executado para SELIC, IGPM, IGPDI, INPC, INCCM, IPCA15
- [✅] Validação visual dos JSONs gerados em `site/data/`
- [✅] PNGs individuais gerados em `site/public/charts/`
- [✅] Categoria `construcao_civil` aparece na home com pelo menos INCC-M
- [✅] Layout não quebra com 9 indicadores em vez de 3

**Smoke test:**

```bash
# Backfill (com pausas para não estressar APIs)
for code in SELIC IGPM IGPDI INPC INCCM IPCA15; do
  python -m pipeline.cli backfill $code
  sleep 5
done

# Build
python -m pipeline.cli build

# Validar contagens
sqlite3 data/indicadores.db "
  SELECT i.code, COUNT(v.id) as n
  FROM indicators i LEFT JOIN indicator_values v ON v.indicator_id = i.id
  GROUP BY i.code ORDER BY i.code;
"

# Validar arquivos
bash scripts/validate-build.sh

# Servir e ver no browser
cd site && npm run dev
# Abrir /, /selic/, /igp-m/, /construcao-civil/
```

---

## Milestone 13 — Filtros de período (Astro Islands)

**Objetivo:** todas as páginas de detalhe têm seletor de período funcionando.

**Entregas:**

- [✅] `site/src/components/PeriodFilter.astro` implementado
- [✅] Tabelas históricas com `id="history-table-{slug}"` consistente
- [✅] Persistência em `localStorage` por slug
- [✅] Default 12 meses
- [✅] Tabela continua renderizada cheia no SSR (hidden via `display:none`)
- [✅] Acessível por teclado e com `aria-pressed`
- [✅] Testes manuais em mobile e desktop
- [✅] Bundle size do JS < 5KB gzipped

**Smoke test:**

```bash
cd site && npm run build
# Inspecionar dist/
# - Cada página de detalhe tem o componente
# - JS inline ou em arquivo único
# - Verificar tamanho:
find dist -name '*.js' -exec gzip -c {} \; | wc -c
# Deve ser bem menor que 5120 bytes

cd site && npx serve dist
# Abrir /ipca/ → testar todos os botões → recarregar página → verificar persistência
# Desabilitar JS no browser → verificar que tabela ainda funciona (cheia)
```

---

## Milestone 14 — Página de comparações

**Objetivo:** `/comparar/` no ar com pelo menos 3 grupos curados.

**Entregas:**

- [✅] `pipeline/config/indicator_groups.py` com 4 grupos definidos
- [✅] `pipeline/core/comparison_charts.py` gera PNGs comparativos
- [✅] Builder estende para gerar `groups.json` e os PNGs `compare-{slug}.png`
- [✅] `site/src/pages/comparar/index.astro` lista os grupos
- [✅] `site/src/pages/comparar/[slug].astro` renderiza cada grupo
- [✅] Item "Comparar" no header de navegação
- [✅] Schema.org Dataset em cada página de comparação
- [✅] PNGs comparativos têm legenda com cores distintas

**Smoke test:**

```bash
python -m pipeline.cli build
ls site/public/charts/compare-*.png
# Esperado: 4 arquivos
cat site/data/groups.json | jq '.groups | length'
# Esperado: 4

cd site && npm run dev
# Abrir /comparar/ → ver os 4 grupos
# Clicar em cada → ver página individual
# Verificar mobile
```

---

## Milestone 15 — Telegram: agendamento configurável

**Objetivo:** controle do cron via comandos do bot.

**Entregas:**

- [✅] `croniter` adicionado ao requirements.txt
- [✅] `pipeline/cli.py` ganha `scheduled-collect` (com gatekeeping via `is_cron_match`)
- [✅] `pipeline/db/connection.py` métodos: `get_active_schedule`, `set_active_schedule`, `set_schedule_enabled`, `update_schedule_run`, `update_schedule_next_run`
- [✅] `pipeline/bot/handlers.py` ganha 4 comandos: `/agendamento`, `/agendar`, `/pausar`, `/retomar`
- [✅] `/status` atualizado para mostrar bloco de agendamento
- [✅] `validate_frequency` rejeita `*/15`, `*`, listas
- [✅] Testes unitários para `scheduled-collect` e handlers

**Smoke test:**

```bash
# Validar que comando funciona
python -m pipeline.cli scheduled-collect
# Se hora atual ≠ 07:00, deve dizer "fora do horário" (skip)

# No Telegram:
# /agendamento → mostra config atual
# /agendar 0 8 * * * → atualiza
# /agendamento → confirma novo cron
# /pausar → desativa
# /agendamento → mostra Pausado
# /retomar → reativa
# /agendar */15 * * * * → rejeitado
```

---

## Milestone 16 — Cron e deploy de Fase 2

**Objetivo:** sistema de Fase 2 100% no ar e operando.

**Entregas:**

- [ ] `scripts/install_cron.sh` atualizado para usar `scheduled-collect` de hora em hora
- [ ] Crontab do notebook atualizado
- [ ] systemd do bot reiniciado (carrega novos handlers)
- [ ] Documentação `09-implementation-plan.md` da raiz: marcar Fase 2 como concluída
- [ ] README atualizado com features novas
- [ ] CHANGELOG.md (se existir) com entrada de Fase 2

**Smoke test:**

```bash
# Atualizar cron
bash scripts/install_cron.sh
crontab -l | grep scheduled-collect

# Restart bot
systemctl --user restart indicadores-bot
systemctl --user status indicadores-bot

# No Telegram:
# /status → mostra 9 indicadores e bloco de agendamento

# Esperar próxima hora cheia → cron dispara → no-op se hora ≠ agendada,
# ou executa se for. Validar via journalctl --user -u indicadores-bot ou pipeline/logs.
```

---

## Definition of Done global da Fase 2

- [ ] 9 indicadores no ar (3 da Fase 1 + 6 da Fase 2)
- [ ] Conector IBGE SIDRA funcionando para IPCA-15
- [ ] Página `/comparar/` com pelo menos 3 grupos curados, charts atualizados a cada build
- [ ] Filtros de período funcionando em todas as páginas de detalhe
- [ ] Telegram com `/agendamento`, `/agendar`, `/pausar`, `/retomar`
- [ ] `scheduled-collect` rodando como cron de hora em hora, gatekeeping funcionando
- [ ] Lighthouse mobile ≥ 95 nas 4 categorias para todas as páginas
- [ ] JS no cliente < 5KB gzipped
- [ ] 7 dias de operação sem incidentes graves após o deploy
- [ ] README atualizado refletindo Fase 2

---

## Backlog Fase 3 (registrado para referência)

Permanece o mesmo do plano original, com pequenos ajustes baseados no que ficou:

- Calculadora de rentabilidade (R$ X corrigido por Y entre datas)
- Gráficos interativos (Chart.js no cliente, substituindo PNGs nas páginas de detalhe)
- Comparação interativa entre indicadores (escolha livre pelo usuário)
- Admin web local
- Conector FGV nativo (apenas se BCB falhar como mirror)
- Migração do IPCA para SIDRA (se houver demanda por dados regionais)
- Indicadores adicionais: PIB, Produção Industrial, PNAD, IPC-Fipe
- Sparklines inline na home

---

## Estimativa de esforço

| Milestone | Complexidade | Tempo de uma sessão de Claude Code |
| --------- | ------------ | ---------------------------------- |
| M10       | Baixa        | 1–2h                               |
| M11       | Média–Alta   | 3–5h                               |
| M12       | Baixa        | 1–2h                               |
| M13       | Média        | 2–3h                               |
| M14       | Média        | 3–4h                               |
| M15       | Média        | 3–4h                               |
| M16       | Baixa        | 1h                                 |

Total estimado: 14–21 horas distribuídas em 7 sessões.

> Estimativas grossas. Variabilidade alta em M11 (SIDRA tem estrutura mais complicada que BCB) e M14 (combinação de pipeline + Astro).
