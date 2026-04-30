# 06 — Telegram Bot: Agendamento Configurável

## Problema

Na Fase 1, o agendamento da coleta diária está fixo no crontab (`0 7 * * *`). Mudar exige SSH no notebook ou editar o arquivo manualmente. Para um operador solo que opera tudo pelo celular, isso é ponto de atrito.

## Solução

O cron passa a chamar um comando `pipeline.cli scheduled-collect` em alta frequência (a cada hora). Esse comando consulta uma tabela `schedule_overrides` no SQLite e decide se deve executar a coleta. O bot Telegram permite editar essa configuração.

## Fluxo

```
crontab (de hora em hora):
0 * * * * cd ~/indicadoreseconomicos && .venv/bin/python -m pipeline.cli scheduled-collect

      ↓

scheduled-collect:
  1. Lê linha ativa de schedule_overrides
  2. Avalia se a hora atual cai na cron expression
  3. Se sim → executa collect --all + publish (mesmo fluxo da Fase 1)
  4. Se não → no-op silencioso (não loga nada exceto em DEBUG)
```

## Schema

Migration `003_schedule_overrides.sql`:

```sql
CREATE TABLE schedule_overrides (
    id              TEXT PRIMARY KEY,
    cron_expression TEXT NOT NULL,        -- cron padrão Unix, ex: "0 7 * * *"
    enabled         INTEGER NOT NULL DEFAULT 1,
    last_run_at     TEXT,
    next_run_at     TEXT,                 -- calculado e atualizado a cada execução
    description     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed da configuração inicial: 07:00 diário (mesma da Fase 1)
INSERT INTO schedule_overrides (id, cron_expression, enabled, description)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    '0 7 * * *',
    1,
    'Agendamento padrão Fase 1'
);
```

> Apenas uma linha em uso por vez. Para histórico/rollback futuro, mantemos como tabela em vez de uma linha em `_config`. Convenção: a linha "ativa" é a única com `enabled = 1` mais recente; as anteriores ficam como histórico (`enabled = 0`).

## CLI: `scheduled-collect`

```python
# pipeline/cli.py

def scheduled_collect(triggered_by: str = "cron"):
    config = db.get_active_schedule()
    if not config or not config.enabled:
        return ScheduledResult(status="paused", reason="agendamento desativado")

    if not is_cron_match(config.cron_expression, datetime.now()):
        return ScheduledResult(status="skipped", reason="fora do horário")

    # Executa o mesmo que collect --all + publish
    collect_results = scheduler.run_all(triggered_by=triggered_by)
    if any(r.added or r.updated for r in collect_results):
        build_result = builder.build()
        if build_result.status == "success":
            deploy_result = builder.deploy(build_result.log_id)
            bot.notify_success(collect_results, build_result, deploy_result)
        else:
            bot.notify_error_build(build_result)
    db.update_schedule_run(config.id, last_run_at=now_iso())
    return ScheduledResult(status="executed", results=collect_results)
```

### Cron matching

Usar a biblioteca `croniter`:

```bash
pip install croniter
```

```python
from croniter import croniter
from datetime import datetime, timedelta

def is_cron_match(expression: str, dt: datetime) -> bool:
    """Verifica se o datetime atual cai dentro da expressão cron (com tolerância de 1h).
    Como o cron real chama de hora em hora, qualquer execução agendada para H:MM dentro
    da hora atual deve ser tratada como match."""
    base = dt.replace(minute=0, second=0, microsecond=0)
    upper = base + timedelta(hours=1)
    iterator = croniter(expression, base - timedelta(seconds=1))
    next_run = iterator.get_next(datetime)
    return base <= next_run < upper
```

## Comandos novos no bot

### `/agendamento`

Mostra a configuração atual.

```
📅 Agendamento atual

Expressão: 0 7 * * *
Em texto: Todos os dias às 07:00
Status: ✅ Ativo
Última execução: 28/04 07:00
Próxima execução: 29/04 07:00

Para alterar: /agendar <expressão cron>
Para pausar: /pausar
```

### `/agendar <cron>`

Define novo agendamento.

```
Usuário: /agendar 0 8,18 * * *

Bot:
✅ Novo agendamento configurado

Expressão: 0 8,18 * * *
Em texto: Todos os dias às 08:00 e 18:00
Próxima execução: 29/04 08:00
```

Validações:
- Sintaxe cron válida (via `croniter`)
- Frequência mínima: 1 execução por hora (`*/15 * * * *` é rejeitado — proteger contra acidentes)
- Frequência máxima: 1 execução por dia mínimo de checagem (não obrigatória)

Se inválido:
```
❌ Expressão cron inválida

Erro: 'foo' não é uma expressão válida.

Exemplos válidos:
- 0 7 * * *      (todo dia às 07:00)
- 0 8,18 * * *   (08:00 e 18:00)
- 0 9 * * 1-5    (segunda a sexta às 09:00)
```

### `/pausar`

Desativa o agendamento (não muda a expressão).

```
⏸ Agendamento pausado

A coleta automática está desativada.
Use /retomar para reativar.

Você ainda pode coletar manualmente com /coletar all.
```

### `/retomar`

Reativa o agendamento.

```
▶️ Agendamento retomado

Expressão atual: 0 7 * * *
Próxima execução: 29/04 07:00
```

### Adições ao `/status`

O comando `/status` da Fase 1 ganha uma seção sobre agendamento:

```
📊 Indicadores Econômicos Hoje

Indicadores ativos: 9
Último deploy: 2026-04-28 07:15

📅 Agendamento: 0 7 * * * (Ativo)
   Próxima execução: 29/04 07:00

Erros nas últimas 24h: 0
```

## Implementação dos handlers

`pipeline/bot/handlers.py`:

```python
from croniter import croniter

@authorized_only
async def cmd_agendamento(update, context):
    cfg = db.get_active_schedule()
    if not cfg:
        await update.message.reply_text("⚠️ Nenhum agendamento configurado. Use /agendar para criar.")
        return
    text = format_schedule(cfg)
    await update.message.reply_text(text, parse_mode="HTML")


@authorized_only
async def cmd_agendar(update, context):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Uso: /agendar <expressão cron>\n"
            "Exemplo: /agendar 0 8,18 * * *"
        )
        return
    expression = " ".join(args)

    # Validação de sintaxe
    try:
        croniter(expression, datetime.now())
    except (ValueError, KeyError) as e:
        await update.message.reply_text(f"❌ Expressão cron inválida: {e}")
        return

    # Validação de frequência mínima (sem mais de 1x/hora)
    if not validate_frequency(expression):
        await update.message.reply_text(
            "❌ Frequência muito alta. Mínimo: 1 execução por hora."
        )
        return

    cfg = db.set_active_schedule(expression, description=None)
    next_run = croniter(expression, datetime.now()).get_next(datetime)
    db.update_schedule_next_run(cfg.id, next_run.isoformat())

    await update.message.reply_text(
        f"✅ Novo agendamento configurado\n\n"
        f"Expressão: <code>{expression}</code>\n"
        f"Próxima execução: {format_dt(next_run)}",
        parse_mode="HTML",
    )


@authorized_only
async def cmd_pausar(update, context):
    db.set_schedule_enabled(False)
    await update.message.reply_text(
        "⏸ Agendamento pausado.\n\n"
        "A coleta automática está desativada. Use /retomar para reativar.\n"
        "Você ainda pode coletar manualmente com /coletar all."
    )


@authorized_only
async def cmd_retomar(update, context):
    cfg = db.get_active_schedule()
    if not cfg:
        await update.message.reply_text("⚠️ Nenhum agendamento configurado. Use /agendar primeiro.")
        return
    db.set_schedule_enabled(True)
    next_run = croniter(cfg.cron_expression, datetime.now()).get_next(datetime)
    await update.message.reply_text(
        f"▶️ Agendamento retomado\n\n"
        f"Expressão atual: <code>{cfg.cron_expression}</code>\n"
        f"Próxima execução: {format_dt(next_run)}",
        parse_mode="HTML",
    )


def validate_frequency(expression: str) -> bool:
    """Garante que a expressão não dispara mais de 1x/hora.
    Heurística simples: o primeiro campo (minutos) deve ser literal único."""
    minutes_field = expression.split()[0]
    # "*" ou intervalos curtos rejeitados
    if minutes_field == "*" or "/" in minutes_field or "," in minutes_field:
        return False
    return True


def format_schedule(cfg) -> str:
    next_run = croniter(cfg.cron_expression, datetime.now()).get_next(datetime) if cfg.enabled else None
    last_run = parse_iso(cfg.last_run_at) if cfg.last_run_at else None
    status_icon = "✅ Ativo" if cfg.enabled else "⏸ Pausado"

    parts = [
        "📅 <b>Agendamento atual</b>",
        "",
        f"Expressão: <code>{cfg.cron_expression}</code>",
        f"Status: {status_icon}",
    ]
    if last_run:
        parts.append(f"Última execução: {format_dt(last_run)}")
    if next_run:
        parts.append(f"Próxima execução: {format_dt(next_run)}")
    parts.extend([
        "",
        "Para alterar: /agendar &lt;expressão cron&gt;",
        "Para pausar: /pausar",
    ])
    return "\n".join(parts)
```

## Mudanças no crontab

Antes (Fase 1):

```
0 7 * * * cd ~/indicadoreseconomicos && .venv/bin/python -m pipeline.cli collect --all && .venv/bin/python -m pipeline.cli publish
```

Depois (Fase 2):

```
0 * * * * cd ~/indicadoreseconomicos && .venv/bin/python -m pipeline.cli scheduled-collect >> ~/indicadoreseconomicos/pipeline/logs/cron.log 2>&1
```

> O cron passa a rodar a cada hora cheia. O comando `scheduled-collect` é o gatekeeper.

> O `scripts/install_cron.sh` (Fase 1) precisa ser atualizado.

## Edge cases

| Cenário | Comportamento |
|---|---|
| Cron expression válida mas próxima execução é em mais de 30 dias | Aceitar (caso de uso legítimo: agendamento mensal) |
| Bot é reiniciado durante coleta agendada | Coleta continua até o fim (executada pelo cron, não pelo bot); bot apenas envia notificação ao voltar |
| `schedule_overrides` está vazio (não inicializado) | `scheduled-collect` é no-op silencioso. `/status` avisa "Nenhum agendamento" |
| Múltiplas linhas com `enabled = 1` (não deveria acontecer) | Usar a mais recente por `updated_at` |
| `croniter` quebra com expressão exótica | `try/except` em todos os pontos; log do erro; `scheduled-collect` continua sem rodar |

## Testes

`pipeline/cli/tests/test_scheduled_collect.py`:

1. Schedule ativo, hora atual bate → executa
2. Schedule ativo, hora não bate → skip
3. Schedule pausado → skip
4. Sem schedule → skip silencioso
5. Cron expression inválida no DB → log de erro, skip

`pipeline/bot/tests/test_handlers_schedule.py`:

1. `/agendar` com expressão válida → atualiza DB
2. `/agendar` com expressão inválida → reply de erro, DB intocado
3. `/agendar` com frequência alta demais → reply de erro
4. `/pausar` desativa
5. `/retomar` reativa
6. `/agendamento` formata corretamente status ativo e pausado

## Migração da operação

Após implantar a Fase 2:

1. Rodar a migration `003_schedule_overrides.sql` (cria a tabela com seed `0 7 * * *`)
2. Editar o crontab (substituir a linha antiga pela nova)
3. Validar via Telegram: `/status` deve mostrar agendamento ativo
4. Esperar 1 hora; cron deve disparar `scheduled-collect`; se for 07:00, executa coleta; se não, no-op silencioso
5. Testar `/agendar 0 8 * * *` e validar que o próximo ciclo às 08:00 rodaria

## Decisão: croniter vs implementação manual

**Escolha**: croniter (~2KB de dependência transitiva).

**Alternativa considerada**: parsing manual da expressão cron.

**Por quê croniter**: sintaxe cron é cheia de edge cases (5 vs 6 campos, ranges, lists, steps). croniter é a referência da comunidade Python e já trata calendário, fuso, etc.
