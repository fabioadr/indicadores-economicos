# CLAUDE.md — Adições da Fase 2

> **Como usar este arquivo**: o conteúdo abaixo deve ser **anexado** ao `CLAUDE.md` da raiz do repositório, não substituí-lo. Recomenda-se adicionar como uma seção dedicada no fim, com cabeçalho `## Fase 2 — Adições e ajustes`.

---

## Fase 2 — Adições e ajustes

A Fase 2 está descrita em `docs/fase2/`. Antes de qualquer trabalho relacionado, leia `docs/fase2/00-README.md` e os docs específicos do escopo.

### Indicadores adicionais

| Code | Slug | Categoria | Conector | Config |
|---|---|---|---|---|
| SELIC | selic | juros | bcb_sgs | series_id 4189 |
| IGPM | igp-m | inflacao | bcb_sgs | series_id 189 |
| IGPDI | igp-di | inflacao | bcb_sgs | series_id 190 |
| INPC | inpc | inflacao | bcb_sgs | series_id 188 |
| INCCM | incc-m | construcao_civil | bcb_sgs | series_id 192 |
| IPCA15 | ipca-15 | inflacao | ibge_sidra | tabela 3065, variavel 355 |

Detalhes completos em `docs/fase2/04-indicators-catalog.md`.

### Conector novo: IBGE SIDRA

Implementado em `pipeline/connectors/ibge_sidra.py`. Registry name: `ibge_sidra`.

Para mapear novos indicadores IBGE, use o subagent `sidra-research` (não inventar tabela/variavel sem validar contra `https://sidra.ibge.gov.br/`).

### Categoria nova: `construcao_civil`

URL: `/construcao-civil/`. Apenas INCC-M na Fase 2; receberá outros indicadores em fases futuras.

### JS no cliente: política revisada

A regra "zero JS" da Fase 1 passa a ser **"JS mínimo no cliente, justificado por feature, sem framework"**. Permitido:

- Filtros de período de tabela (Astro Islands com vanilla TS)
- Persistência em `localStorage` para preferências de UI

Não permitido:
- Frameworks (React/Vue/Svelte) no cliente — manter Astro puro
- Bundle gzipped acima de 5KB total
- JS para conteúdo principal (HTML deve continuar funcional sem JS)

### Página nova: `/comparar/`

Comparações pré-renderizadas em PNG, configuradas em `pipeline/config/indicator_groups.py`. Adicionar/remover grupos é uma alteração de código + redeploy.

Para adicionar novos grupos, use a skill `add-comparison-group`.

### Agendamento configurável

Crontab da Fase 2 chama `pipeline.cli scheduled-collect` de hora em hora. O comando consulta `schedule_overrides` no DB e decide se executa.

Operação via Telegram: `/agendamento`, `/agendar <cron>`, `/pausar`, `/retomar`.

**Não editar o crontab manualmente para alterar horário** — usar `/agendar` no Telegram.

### Comandos comuns adicionados

```bash
# Coleta gateada por agendamento (substitui collect --all no cron)
python -m pipeline.cli scheduled-collect

# Forçar regeneração apenas das comparações (pula coleta + indicadores individuais)
bash scripts/regenerate-comparisons.sh

# Validação estendida (Fase 1 + Fase 2)
bash scripts/validate-fase2-build.sh
```

### Dependências adicionadas

Em `pipeline/requirements.txt`:

```
croniter
```

Em `site/package.json`: nada novo (Astro Islands é nativo).

### Coisas a NÃO fazer (adendos)

- ❌ Não migrar IPCA da Fase 1 para SIDRA — é decisão explícita de não fazer agora
- ❌ Não construir conector FGV nativo na Fase 2 — usar BCB SGS como espelho
- ❌ Não introduzir frameworks JS no cliente — manter Astro Islands com vanilla TS
- ❌ Não permitir comparações combinatórias livres — apenas grupos curados, pré-renderizados
- ❌ Não permitir frequência de cron acima de 1x/hora via `/agendar`

### Quando estiver em dúvida (ajuste ao da Fase 1)

Antes de implementar features de Fase 2, valide nesta ordem:
1. `docs/fase2/01-vision-and-scope.md` — está dentro do escopo?
2. `docs/fase2/02-architecture-deltas.md` — encaixa nos deltas previstos?
3. `docs/fase2/07-implementation-plan.md` — está dentro do milestone certo?
4. Se nenhum dos três cobre, **perguntar antes de implementar**

### Indicadores Fase 2 — referência rápida

| Code | Série/Tabela | Inception |
|---|---|---|
| SELIC | BCB SGS 4189 | 1986-06 |
| IGPM | BCB SGS 189 | 1989-06 |
| IGPDI | BCB SGS 190 | 1944-02 |
| INPC | BCB SGS 188 | 1979-04 |
| INCCM | BCB SGS 192 | 1989-06 |
| IPCA15 | SIDRA 3065/355 | 2000-05 |

> Sempre confirmar via subagent (`bcb-research` ou `sidra-research`) antes de aplicar mudanças no DB.
