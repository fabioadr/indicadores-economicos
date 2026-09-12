"""Derivados do salário mínimo: vigências (degraus) e destaques da página.

Não são séries coletadas. O valor diário usa a base de 30 dias e o horário a
jornada de 44 horas semanais (mensal / 220), convenção da CLT para mensalista.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

DAY_DIVISOR = 30
HOUR_DIVISOR = 220


class _Point(Protocol):
    reference_date: date
    value: float


def derive_steps(values: list[_Point]) -> list[dict]:
    """Uma linha por vigência (valor constante consecutivo). Mais recente primeiro."""
    if not values:
        return []

    ordered = sorted(values, key=lambda v: v.reference_date)
    groups: list[list[_Point]] = []
    current = [ordered[0]]
    for point in ordered[1:]:
        if _same_money(point.value, current[-1].value):
            current.append(point)
        else:
            groups.append(current)
            current = [point]
    groups.append(current)

    steps: list[dict] = []
    prev_value: float | None = None
    for group in groups:
        value = group[-1].value
        steps.append({
            "from": group[0].reference_date.isoformat(),
            "until": group[-1].reference_date.isoformat(),
            "value": value,
            "change_brl": None if prev_value is None else round(value - prev_value, 2),
            "change_pct": None if prev_value is None else _pct(value, prev_value),
        })
        prev_value = value
    steps.reverse()
    return steps


def derive_highlights(values: list[_Point]) -> dict | None:
    """Valor vigente, dia, hora e reajuste do último degrau."""
    if not values:
        return None

    ordered = sorted(values, key=lambda v: v.reference_date)
    latest = ordered[-1].value
    previous: float | None = None
    for point in reversed(ordered[:-1]):
        if not _same_money(point.value, latest):
            previous = point.value
            break

    return {
        "monthly": latest,
        "daily": latest / DAY_DIVISOR,
        "hourly": latest / HOUR_DIVISOR,
        "day_divisor": DAY_DIVISOR,
        "hour_divisor": HOUR_DIVISOR,
        "previous_value": previous,
        "adjustment_brl": None if previous is None else round(latest - previous, 2),
        "adjustment_pct": None if previous is None else _pct(latest, previous),
    }


def _same_money(a: float, b: float) -> bool:
    return round(a, 2) == round(b, 2)


def _pct(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current / previous - 1) * 100
