"""Recompute YTD / last_12m / last_24m / since_inception for an indicator.

Spec: docs/03-data-model.md (cálculo das agregações) and docs/05-pipeline.md.
All Phase 1 indicators are monthly percentages composed geometrically.
"""

from __future__ import annotations

import sqlite3

from pipeline.db.connection import (
    batch_update_aggregations,
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


def recompute_aggregations(conn: sqlite3.Connection, indicator_id: str) -> None:
    values = list_values(conn, indicator_id, order="asc")
    if not values:
        return

    inception_factor = 1.0
    by_year: dict[int, list[float]] = {}
    updates: list[tuple[str, float | None, float | None, float | None, float]] = []

    for i, v in enumerate(values):
        inception_factor *= 1 + v.value / 100
        since_inception = (inception_factor - 1) * 100

        year = v.reference_date.year
        by_year.setdefault(year, []).append(v.value)
        ytd = accumulate(by_year[year])

        last_12_window = values[max(0, i - 11) : i + 1]
        last_12m = (
            accumulate([x.value for x in last_12_window])
            if len(last_12_window) == 12
            else None
        )

        last_24_window = values[max(0, i - 23) : i + 1]
        last_24m = (
            accumulate([x.value for x in last_24_window])
            if len(last_24_window) == 24
            else None
        )

        updates.append((v.id, ytd, last_12m, last_24m, since_inception))

    batch_update_aggregations(conn, updates)
