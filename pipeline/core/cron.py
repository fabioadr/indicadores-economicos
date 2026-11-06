"""Utilitários puros de cron para o gatekeeper `scheduled-collect` e validação no bot.

Não fazem I/O — fáceis de testar.

Convenções:
- O cron real do sistema dispara `scheduled-collect` de hora em hora (`0 * * * *`).
- `is_due` decide se o `scheduled-collect` deve coletar: True se a execução
  agendada mais recente (<= agora) ainda não foi feita (`last_run` anterior a ela).
  Isso recupera execuções perdidas: o host é um desktop e o WSL só sobe após o
  logon, então a hora exata agendada muitas vezes passa com a máquina desligada.
- `is_cron_match` (janela da hora atual) fica para validações pontuais.
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


def is_due(expression: str, now: datetime, last_run: datetime | None) -> bool:
    """True se a execução agendada mais recente (<= `now`) ainda não rodou.

    Coleta é idempotente, então rodar atrasado (catch-up) é seguro; várias
    execuções perdidas viram uma só.
    """
    latest_scheduled = croniter(expression, now + timedelta(seconds=1)).get_prev(datetime)
    return last_run is None or last_run < latest_scheduled


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
