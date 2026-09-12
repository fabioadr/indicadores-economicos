"""Derivados do salário mínimo: vigências e destaques."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pipeline.core.wage import DAY_DIVISOR, HOUR_DIVISOR, derive_highlights, derive_steps


@dataclass
class _Point:
    reference_date: date
    value: float


def _series() -> list[_Point]:
    """Três vigências: 1412 (2024), 1518 (2025), 1621 (jan–set/2026)."""
    points: list[_Point] = []
    for month in range(1, 13):
        points.append(_Point(date(2024, month, 1), 1412.0))
        points.append(_Point(date(2025, month, 1), 1518.0))
    for month in range(1, 10):
        points.append(_Point(date(2026, month, 1), 1621.0))
    return points


def test_highlights_2026_step():
    highlights = derive_highlights(_series())
    assert highlights is not None
    assert highlights["monthly"] == 1621.0
    assert highlights["day_divisor"] == DAY_DIVISOR == 30
    assert highlights["hour_divisor"] == HOUR_DIVISOR == 220
    assert round(highlights["daily"], 2) == 54.03
    assert round(highlights["hourly"], 2) == 7.37
    assert highlights["previous_value"] == 1518.0
    assert highlights["adjustment_brl"] == 103.0
    assert round(highlights["adjustment_pct"], 2) == 6.79


def test_steps_collapse_identical_months():
    steps = derive_steps(_series())
    assert [s["value"] for s in steps] == [1621.0, 1518.0, 1412.0]
    current = steps[0]
    assert current["from"] == "2026-01-01"
    assert current["until"] == "2026-09-01"
    assert current["change_brl"] == 103.0
    assert round(current["change_pct"], 2) == 6.79
    assert steps[-1]["change_brl"] is None
    assert steps[-1]["change_pct"] is None
    assert steps[1]["from"] == "2025-01-01"
    assert steps[1]["until"] == "2025-12-01"


def test_empty_series():
    assert derive_steps([]) == []
    assert derive_highlights([]) is None
