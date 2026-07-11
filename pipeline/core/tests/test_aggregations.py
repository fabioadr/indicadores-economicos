"""Tests for aggregation logic and persistence helpers (M3)."""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import pytest

from pipeline.connectors.base import RawDataPoint
from pipeline.core.aggregations import accumulate, pct_change, recompute_aggregations
from pipeline.db.connection import (
    apply_pending_migrations,
    get_connection,
    get_last_value_date,
    list_values,
    upsert_value,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"

DUMMY_INDICATOR_ID = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "indicadores.db"
    conn = get_connection(db_path)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    conn.execute(
        """
        INSERT INTO indicators (
            id, code, slug, name, short_description, long_description,
            category, unit, frequency, source_name, source_url,
            connector_type, connector_config, inception_date,
            active, meta_title, meta_description
        ) VALUES (?, 'TEST', 'test', 'Test', '.', '.', 'inflacao', 'percent',
                  'monthly', 'src', 'http://x', 'bcb_sgs', '{}',
                  '2000-01-01', 1, 't', 'd')
        """,
        (DUMMY_INDICATOR_ID,),
    )
    conn.commit()
    yield conn
    conn.close()


def _insert_series(conn, points: list[tuple[date, float]]) -> None:
    for d, v in points:
        upsert_value(conn, DUMMY_INDICATOR_ID, RawDataPoint(d, v, str(v)))


def test_accumulate_basic_geometric_composition():
    # (1.005 * 1.003 * 1.004 - 1) * 100 ≈ 1.20471
    assert accumulate([0.5, 0.3, 0.4]) == pytest.approx(1.20471, abs=1e-4)


def test_accumulate_single_value_equals_input():
    assert accumulate([0.42]) == pytest.approx(0.42)


def test_accumulate_empty_returns_zero():
    assert accumulate([]) == 0.0


def test_get_last_value_date_none_for_empty(db_conn):
    assert get_last_value_date(db_conn, DUMMY_INDICATOR_ID) is None


def test_upsert_returns_existed_flag(db_conn):
    point = RawDataPoint(date(2025, 1, 1), 0.5, "0.5")
    assert upsert_value(db_conn, DUMMY_INDICATOR_ID, point) is False

    updated = RawDataPoint(date(2025, 1, 1), 0.6, "0.6")
    assert upsert_value(db_conn, DUMMY_INDICATOR_ID, updated) is True

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    assert len(rows) == 1
    assert rows[0].value == 0.6
    assert rows[0].raw_value == "0.6"


def test_get_last_value_date_returns_max(db_conn):
    _insert_series(
        db_conn,
        [
            (date(2024, 1, 1), 0.1),
            (date(2024, 3, 1), 0.2),
            (date(2024, 2, 1), 0.3),
        ],
    )
    assert get_last_value_date(db_conn, DUMMY_INDICATOR_ID) == date(2024, 3, 1)


def test_ytd_resets_per_year(db_conn):
    _insert_series(
        db_conn,
        [
            (date(2024, 11, 1), 0.5),
            (date(2024, 12, 1), 0.4),
            (date(2025, 1, 1), 0.3),
            (date(2025, 2, 1), 0.2),
        ],
    )
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    by_date = {v.reference_date: v for v in list_values(db_conn, DUMMY_INDICATOR_ID)}
    assert by_date[date(2024, 11, 1)].ytd == pytest.approx(accumulate([0.5]))
    assert by_date[date(2024, 12, 1)].ytd == pytest.approx(accumulate([0.5, 0.4]))
    # YTD restarts in 2025
    assert by_date[date(2025, 1, 1)].ytd == pytest.approx(accumulate([0.3]))
    assert by_date[date(2025, 2, 1)].ytd == pytest.approx(accumulate([0.3, 0.2]))


def test_last_12m_null_until_full_window(db_conn):
    series = [(date(2024, m, 1), 0.4) for m in range(1, 12)]  # 11 months
    series.append((date(2024, 12, 1), 0.4))  # 12th month -> window complete
    series.append((date(2025, 1, 1), 0.4))  # 13th month -> still complete
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    # First 11 rows have NULL last_12m
    for row in rows[:11]:
        assert row.last_12m is None
    # 12th and 13th rows have the geometric accumulation of 12 values of 0.4%
    expected = accumulate([0.4] * 12)
    assert rows[11].last_12m == pytest.approx(expected)
    assert rows[12].last_12m == pytest.approx(expected)


def test_last_24m_null_until_full_window(db_conn):
    # 23 monthly values -> all last_24m must be NULL.
    series = []
    cur = date(2023, 1, 1)
    for _ in range(23):
        series.append((cur, 0.3))
        # advance one month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    assert all(r.last_24m is None for r in rows)

    # Add the 24th -> the last row should now have a non-NULL last_24m.
    upsert_value(db_conn, DUMMY_INDICATOR_ID, RawDataPoint(cur, 0.3, "0.3"))
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)
    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    assert rows[-1].last_24m == pytest.approx(accumulate([0.3] * 24))
    # Earlier rows still NULL.
    assert all(r.last_24m is None for r in rows[:-1])


def test_since_inception_matches_full_accumulate(db_conn):
    series = [
        (date(2023, 1, 1), 0.5),
        (date(2023, 2, 1), 0.3),
        (date(2023, 3, 1), 0.4),
        (date(2024, 1, 1), 0.2),
    ]
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    expected_last = accumulate([v for _, v in series])
    assert rows[-1].since_inception == pytest.approx(expected_last)
    # Monotonic growth for positive percentages.
    sis = [r.since_inception for r in rows]
    assert all(b >= a for a, b in zip(sis, sis[1:]))
    # First row's since_inception equals its own value.
    assert rows[0].since_inception == pytest.approx(0.5)


def test_recompute_overwrites_previous_aggregations(db_conn):
    """A new value at the end must propagate to last_12m of earlier rows."""
    series = [(date(2024, m, 1), 0.4) for m in range(1, 13)]
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    before = list_values(db_conn, DUMMY_INDICATOR_ID)
    # The 12th has last_12m, the 11th does not.
    assert before[10].last_12m is None
    assert before[11].last_12m is not None

    # Insert one more month -> still no change for early rows; last row has new last_12m.
    upsert_value(db_conn, DUMMY_INDICATOR_ID, RawDataPoint(date(2025, 1, 1), 0.4, "0.4"))
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    after = list_values(db_conn, DUMMY_INDICATOR_ID)
    assert len(after) == 13
    assert after[10].last_12m is None
    assert after[12].last_12m == pytest.approx(accumulate([0.4] * 12))
    # since_inception should have been recomputed for every row and grown.
    assert after[-1].since_inception > before[-1].since_inception
    # Sanity: floats are finite.
    assert math.isfinite(after[-1].since_inception)


# ---------------------------------------------------------------------------
# aggregation_mode = "none" (SELIC anualizada)
# ---------------------------------------------------------------------------


def test_aggregation_mode_none_writes_null(db_conn):
    db_conn.execute(
        "UPDATE indicators SET aggregation_mode = 'none' WHERE id = ?",
        (DUMMY_INDICATOR_ID,),
    )
    db_conn.commit()

    _insert_series(
        db_conn,
        [
            (date(2025, 1, 1), 14.9),
            (date(2025, 2, 1), 14.9),
            (date(2025, 3, 1), 14.8),
        ],
    )
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    for r in rows:
        assert r.ytd is None
        assert r.last_12m is None
        assert r.last_24m is None
        assert r.since_inception is None


# ---------------------------------------------------------------------------
# aggregation_mode = "compound_daily_to_monthly" (TR diária)
# ---------------------------------------------------------------------------


def test_aggregation_mode_daily_to_monthly_reduces_to_last_of_month(db_conn):
    """O último valor de cada mês é o que entra na composição mensal."""
    db_conn.execute(
        "UPDATE indicators SET aggregation_mode = 'compound_daily_to_monthly' "
        "WHERE id = ?",
        (DUMMY_INDICATOR_ID,),
    )
    db_conn.commit()

    # Jan/2025: três valores diários, último = 0.20
    # Fev/2025: dois valores, último = 0.30
    series = [
        (date(2025, 1, 5), 0.10),
        (date(2025, 1, 15), 0.15),
        (date(2025, 1, 28), 0.20),
        (date(2025, 2, 10), 0.25),
        (date(2025, 2, 27), 0.30),
    ]
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    by_date = {r.reference_date: r for r in rows}

    # YTD do final de jan/2025 = composição apenas do último de jan
    expected_jan_ytd = accumulate([0.20])
    assert by_date[date(2025, 1, 28)].ytd == pytest.approx(expected_jan_ytd)

    # YTD do final de fev/2025 = composição (0.20, 0.30)
    expected_feb_ytd = accumulate([0.20, 0.30])
    assert by_date[date(2025, 2, 27)].ytd == pytest.approx(expected_feb_ytd)

    # Os valores diários intermediários herdam o YTD do mês a que pertencem
    assert by_date[date(2025, 1, 5)].ytd == pytest.approx(expected_jan_ytd)
    assert by_date[date(2025, 1, 15)].ytd == pytest.approx(expected_jan_ytd)
    assert by_date[date(2025, 2, 10)].ytd == pytest.approx(expected_feb_ytd)


def test_aggregation_mode_daily_to_monthly_last_12m_uses_monthly_window(db_conn):
    """last_12m precisa de 12 meses distintos, não 12 valores diários."""
    db_conn.execute(
        "UPDATE indicators SET aggregation_mode = 'compound_daily_to_monthly' "
        "WHERE id = ?",
        (DUMMY_INDICATOR_ID,),
    )
    db_conn.commit()

    # 30 valores diários de jan/2025 — apenas 1 mês, last_12m deve ser None.
    series = [(date(2025, 1, d), 0.10) for d in range(1, 31)]
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    assert all(r.last_12m is None for r in rows)

    # Adiciona 11 meses cobrindo fev/2025..dez/2025 → 12 meses no total →
    # last_12m do último valor passa a ser o produto dos 12 últimos de cada mês.
    extra = [(date(2025, m, 15), 0.10) for m in range(2, 13)]
    _insert_series(db_conn, extra)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    last = rows[-1]
    assert last.last_12m == pytest.approx(accumulate([0.10] * 12))


# ---------------------------------------------------------------------------
# aggregation_mode = "level" (saldo / índice absoluto)
# ---------------------------------------------------------------------------


def test_pct_change_basic():
    assert pct_change(110.0, 100.0) == pytest.approx(10.0)
    assert pct_change(100.0, 0.0) is None


def test_aggregation_mode_level_ytd_from_prior_december(db_conn):
    db_conn.execute(
        "UPDATE indicators SET aggregation_mode = 'level', unit = 'brl_millions' "
        "WHERE id = ?",
        (DUMMY_INDICATOR_ID,),
    )
    db_conn.commit()

    _insert_series(
        db_conn,
        [
            (date(2024, 12, 1), 1000.0),
            (date(2025, 1, 1), 1050.0),
            (date(2025, 2, 1), 1100.0),
        ],
    )
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    by_date = {v.reference_date: v for v in list_values(db_conn, DUMMY_INDICATOR_ID)}
    # Dez/2024: sem dez anterior → base = próprio 1º ponto do ano → 0%
    assert by_date[date(2024, 12, 1)].ytd == pytest.approx(0.0)
    assert by_date[date(2025, 1, 1)].ytd == pytest.approx(5.0)
    assert by_date[date(2025, 2, 1)].ytd == pytest.approx(10.0)


def test_aggregation_mode_level_last_12m_and_since_inception(db_conn):
    db_conn.execute(
        "UPDATE indicators SET aggregation_mode = 'level', unit = 'index' "
        "WHERE id = ?",
        (DUMMY_INDICATOR_ID,),
    )
    db_conn.commit()

    # 13 meses: índice sobe de 100 → 112
    series = [(date(2024, m, 1), 100.0 + m) for m in range(1, 13)]
    series.append((date(2025, 1, 1), 112.0))
    _insert_series(db_conn, series)
    recompute_aggregations(db_conn, DUMMY_INDICATOR_ID)

    rows = list_values(db_conn, DUMMY_INDICATOR_ID)
    for row in rows[:12]:
        assert row.last_12m is None
    # Jan/2025 (112) vs Jan/2024 (101)
    assert rows[12].last_12m == pytest.approx(pct_change(112.0, 101.0))
    assert rows[0].since_inception == pytest.approx(0.0)
    assert rows[-1].since_inception == pytest.approx(pct_change(112.0, 101.0))
