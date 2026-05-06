"""Utilitários puros de cron para o gatekeeper `scheduled-collect` e validação no bot.

Não fazem I/O — fáceis de testar.

Convenções:
- O cron real do sistema dispara `scheduled-collect` de hora em hora (`0 * * * *`).
- `is_cron_match` retorna True se a expressão configurada tem alguma execução
  agendada dentro da hora atual.
- Tz: usamos `datetime.now()` naive — mesma tz do processo (e portanto do cron).
  Se o notebook estiver em UTC e o usuário esperar America/Sao_Paulo, a coleta
  dispara em horário deslocado. Operacional, não de código.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from croniter import croniter


def is_cron_match(expression: str, dt: datetime) -> bool:
    """True se há alguma execução agendada dentro da janela [hora_de(dt), +1h).

    Como o cron real chama de hora em hora, qualquer execução agendada para
    H:MM (M = 0..59) na hora atual deve ser tratada como match.
    """
    base = dt.replace(minute=0, second=0, microsecond=0)
    upper = base + timedelta(hours=1)
    iterator = croniter(expression, base - timedelta(seconds=1))
    next_run = iterator.get_next(datetime)
    return base <= next_run < upper


def validate_frequency(expression: str) -> bool:
    """False se o campo de minutos permite mais de 1 execução por hora.

    Heurística: o primeiro campo (minutos) precisa ser literal único.
    Rejeita `*`, ranges com `/` (`*/15`) e listas (`0,30`).
    """
    parts = expression.split()
    if not parts:
        return False
    minutes_field = parts[0]
    if minutes_field == "*" or "/" in minutes_field or "," in minutes_field or "-" in minutes_field:
        return False
    return True


def next_run(expression: str, dt: datetime) -> datetime:
    """Próxima execução da expressão a partir de `dt`."""
    return croniter(expression, dt).get_next(datetime)
