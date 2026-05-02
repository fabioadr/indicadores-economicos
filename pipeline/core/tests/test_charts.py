"""Smoke tests for chart generation: produces valid PNG files."""

from __future__ import annotations

from datetime import date

from pipeline.core import charts
from pipeline.db.connection import IndicatorValue


PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def _make_values(n: int) -> list[IndicatorValue]:
    out: list[IndicatorValue] = []
    factor = 1.0
    for i in range(n):
        year = 2025 + i // 12
        month = (i % 12) + 1
        value = 0.30 + 0.02 * (i % 6)
        factor *= 1 + value / 100
        out.append(
            IndicatorValue(
                id=f"v{i}",
                indicator_id="ind",
                reference_date=date(year, month, 1),
                value=value,
                ytd=None,
                last_12m=value * 12 if i >= 11 else None,
                last_24m=None,
                since_inception=(factor - 1) * 100,
                raw_value=None,
            )
        )
    return out


def test_current_year_chart_writes_png(tmp_path):
    values = _make_values(15)
    out = tmp_path / "ipca-2026.png"
    charts.generate_chart_current_year(values, "inflacao", 2026, out)
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_history_chart_writes_png(tmp_path):
    values = _make_values(24)
    out = tmp_path / "ipca-history.png"
    charts.generate_chart_history(values, "inflacao", out)
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_current_year_chart_with_no_year_data(tmp_path):
    values = _make_values(3)  # all in 2025
    out = tmp_path / "x-2030.png"
    charts.generate_chart_current_year(values, "juros", 2030, out)
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_current_year_chart_mode_none_writes_png(tmp_path):
    values = _make_values(15)
    out = tmp_path / "selic-2026.png"
    charts.generate_chart_current_year(
        values, "juros", 2026, out, aggregation_mode="none"
    )
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_history_chart_mode_none_writes_png(tmp_path):
    values = _make_values(24)
    out = tmp_path / "selic-history.png"
    charts.generate_chart_history(
        values, "juros", out, aggregation_mode="none"
    )
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def _make_daily_values(months: int, days_per_month: int = 25) -> list[IndicatorValue]:
    """Multiple daily values per month, mimicking TR shape."""
    out: list[IndicatorValue] = []
    idx = 0
    for m_offset in range(months):
        year = 2025 + m_offset // 12
        month = (m_offset % 12) + 1
        for d in range(1, days_per_month + 1):
            out.append(
                IndicatorValue(
                    id=f"d{idx}",
                    indicator_id="ind",
                    reference_date=date(year, month, d),
                    value=0.16,
                    ytd=None,
                    last_12m=2.0 if m_offset >= 11 else None,
                    last_24m=None,
                    since_inception=None,
                    raw_value=None,
                )
            )
            idx += 1
    return out


def test_history_chart_daily_to_monthly_writes_png(tmp_path):
    values = _make_daily_values(months=14)
    out = tmp_path / "tr-history.png"
    charts.generate_chart_history(
        values, "correcao_monetaria", out,
        aggregation_mode="compound_daily_to_monthly",
    )
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_current_year_chart_daily_to_monthly_writes_png(tmp_path):
    values = _make_daily_values(months=14)
    out = tmp_path / "tr-2026.png"
    charts.generate_chart_current_year(
        values, "correcao_monetaria", 2026, out,
        aggregation_mode="compound_daily_to_monthly",
    )
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER
