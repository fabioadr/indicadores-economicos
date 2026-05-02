"""Recompute YTD / last_12m / last_24m / since_inception for an indicator.

Spec: docs/03-data-model.md (cálculo das agregações) and docs/05-pipeline.md.
A maioria dos indicadores são variações mensais compostas geometricamente.
Casos especiais (controlados via `indicators.aggregation_mode`):

- ``compound_monthly`` (default): comportamento original — compõe todos os
  valores cronologicamente.
- ``compound_daily_to_monthly``: a série tem múltiplos valores por mês (ex: TR
  diária). Reduzimos a 1 valor por mês (último do mês) **antes** de compor
  YTD/12m/24m/since_inception. Os valores diários permanecem na tabela; só as
  agregações mudam.
- ``none``: a série não admite composição (ex: SELIC anualizada). Gravamos
  ``NULL`` em todas as colunas agregadas.
"""

from __future__ import annotations

import sqlite3
from datetime import date

from pipeline.db.connection import (
    IndicatorValue,
    batch_update_aggregations,
    fetch_one,
    list_values,
)


def accumulate(percentages: list[float]) -> float:
    """Geometric composition: ((∏(1 + p/100)) − 1) * 100.

    Empty input returns 0.0 — caller decides whether to surface it as NULL.
    """
    factor = 1.0
    for p in percentages:
        factor *= 1 + p / 100
    return (factor - 1) * 100


def _get_aggregation_mode(conn: sqlite3.Connection, indicator_id: str) -> str:
    row = fetch_one(
        conn,
        "SELECT aggregation_mode FROM indicators WHERE id = ?",
        (indicator_id,),
    )
    if row is None:
        return "compound_monthly"
    return row["aggregation_mode"] or "compound_monthly"


def _null_aggregations(values: list[IndicatorValue]) -> list[
    tuple[str, float | None, float | None, float | None, float | None]
]:
    return [(v.id, None, None, None, None) for v in values]


def _reduce_daily_to_monthly(
    values: list[IndicatorValue],
) -> list[IndicatorValue]:
    """Mantém apenas o último valor de cada (ano, mês), preservando a ordem."""
    by_month: dict[tuple[int, int], IndicatorValue] = {}
    for v in values:
        key = (v.reference_date.year, v.reference_date.month)
        by_month[key] = v  # later iterations overwrite earlier ones
    return sorted(by_month.values(), key=lambda v: v.reference_date)


def _compound_updates(
    monthly_values: list[IndicatorValue],
) -> list[tuple[str, float | None, float | None, float | None, float | None]]:
    """Calcula YTD/12m/24m/since_inception assumindo 1 valor por mês."""
    inception_factor = 1.0
    by_year: dict[int, list[float]] = {}
    updates: list[
        tuple[str, float | None, float | None, float | None, float | None]
    ] = []

    for i, v in enumerate(monthly_values):
        inception_factor *= 1 + v.value / 100
        since_inception = (inception_factor - 1) * 100

        year = v.reference_date.year
        by_year.setdefault(year, []).append(v.value)
        ytd = accumulate(by_year[year])

        last_12_window = monthly_values[max(0, i - 11) : i + 1]
        last_12m = (
            accumulate([x.value for x in last_12_window])
            if len(last_12_window) == 12
            else None
        )

        last_24_window = monthly_values[max(0, i - 23) : i + 1]
        last_24m = (
            accumulate([x.value for x in last_24_window])
            if len(last_24_window) == 24
            else None
        )

        updates.append((v.id, ytd, last_12m, last_24m, since_inception))
    return updates


def _propagate_monthly_to_all(
    all_values: list[IndicatorValue],
    monthly_updates: list[
        tuple[str, float | None, float | None, float | None, float | None]
    ],
) -> list[tuple[str, float | None, float | None, float | None, float | None]]:
    """Para o modo daily_to_monthly: cada valor diário herda as agregações do
    seu (ano, mês). Assim a UI/JSON não veem ``NULL`` em dias intermediários.
    """
    monthly_id_to_agg: dict[str, tuple[
        float | None, float | None, float | None, float | None
    ]] = {row[0]: row[1:] for row in monthly_updates}
    monthly_id_to_month: dict[tuple[int, int], str] = {}
    # Reconstruct id -> (year, month) by walking all_values
    id_to_date: dict[str, date] = {v.id: v.reference_date for v in all_values}
    for monthly_id in monthly_id_to_agg:
        d = id_to_date[monthly_id]
        monthly_id_to_month[(d.year, d.month)] = monthly_id

    updates: list[
        tuple[str, float | None, float | None, float | None, float | None]
    ] = []
    for v in all_values:
        key = (v.reference_date.year, v.reference_date.month)
        anchor_id = monthly_id_to_month.get(key)
        if anchor_id is None:
            updates.append((v.id, None, None, None, None))
            continue
        ytd, l12, l24, si = monthly_id_to_agg[anchor_id]
        updates.append((v.id, ytd, l12, l24, si))
    return updates


def recompute_aggregations(conn: sqlite3.Connection, indicator_id: str) -> None:
    values = list_values(conn, indicator_id, order="asc")
    if not values:
        return

    mode = _get_aggregation_mode(conn, indicator_id)

    if mode == "none":
        batch_update_aggregations(conn, _null_aggregations(values))
        return

    if mode == "compound_daily_to_monthly":
        monthly = _reduce_daily_to_monthly(values)
        monthly_updates = _compound_updates(monthly)
        updates = _propagate_monthly_to_all(values, monthly_updates)
        batch_update_aggregations(conn, updates)
        return

    # default: compound_monthly
    batch_update_aggregations(conn, _compound_updates(values))
