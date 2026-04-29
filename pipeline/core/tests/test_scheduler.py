"""Tests for the scheduler (M4): should_collect, collect_single, run_all."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import respx

from pipeline.connectors.bcb import BCB_BASE_URL
from pipeline.core import scheduler
from pipeline.db.connection import (
    Indicator,
    apply_pending_migrations,
    fetch_all,
    get_connection,
    get_indicator_by_code,
    list_values,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture(autouse=True)
def _no_pagination_pause(monkeypatch):
    monkeypatch.setattr("pipeline.connectors.bcb.time.sleep", lambda _: None)


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "indicadores.db"
    conn = get_connection(db_path)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()


def _ind(**overrides) -> Indicator:
    base = dict(
        id="i-1",
        code="TEST",
        slug="test",
        name="Test",
        category="inflacao",
        frequency="monthly",
        connector_type="bcb_sgs",
        connector_config='{"series_id": 999}',
        inception_date=__import__("datetime").date(2020, 1, 1),
        expected_release_day=10,
        active=True,
        last_collected_at=None,
    )
    base.update(overrides)
    return Indicator(**base)


# ---------------------------------------------------------------------------
# should_collect
# ---------------------------------------------------------------------------


def test_should_collect_true_when_never_collected():
    assert scheduler.should_collect(_ind(last_collected_at=None)) is True


def test_should_collect_daily_threshold():
    now = datetime(2025, 1, 10, 12, 0, tzinfo=timezone.utc)
    fresh = (now - timedelta(hours=10)).isoformat()
    stale = (now - timedelta(hours=21)).isoformat()
    assert (
        scheduler.should_collect(
            _ind(frequency="daily", last_collected_at=fresh), now=now
        )
        is False
    )
    assert (
        scheduler.should_collect(
            _ind(frequency="daily", last_collected_at=stale), now=now
        )
        is True
    )


def test_should_collect_biweekly_threshold():
    now = datetime(2025, 1, 30, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(days=10)).isoformat()
    old = (now - timedelta(days=15)).isoformat()
    assert (
        scheduler.should_collect(
            _ind(frequency="biweekly", last_collected_at=recent), now=now
        )
        is False
    )
    assert (
        scheduler.should_collect(
            _ind(frequency="biweekly", last_collected_at=old), now=now
        )
        is True
    )


def test_should_collect_monthly_recent_returns_false():
    now = datetime(2025, 4, 15, 12, 0, tzinfo=timezone.utc)
    last = (now - timedelta(hours=12)).isoformat()
    # Sem precisar de conn: <24h sempre False.
    assert (
        scheduler.should_collect(
            _ind(frequency="monthly", last_collected_at=last), now=now
        )
        is False
    )


def test_should_collect_monthly_retries_until_value_arrives(db_conn):
    db_conn.execute(
        """
        INSERT INTO indicators (
            id, code, slug, name, short_description, long_description,
            category, unit, frequency, source_name, source_url,
            connector_type, connector_config, inception_date, active,
            meta_title, meta_description
        ) VALUES (
            'mon-1', 'MON', 'mon', 'Monthly test', '.', '.',
            'inflacao', 'percent', 'monthly', 'src', 'http://x',
            'bcb_sgs', '{}', '2020-01-01', 1, 't', 'd'
        )
        """
    )
    db_conn.commit()

    indicator = get_indicator_by_code(db_conn, "MON")
    now = datetime(2025, 4, 15, 12, 0, tzinfo=timezone.utc)
    last = (now - timedelta(days=2)).isoformat()
    indicator.last_collected_at = last

    # Sem o valor de março/2025 → re-tenta hoje.
    assert scheduler.should_collect(indicator, conn=db_conn, now=now) is True

    # Insere o valor do mês anterior → só re-coleta após 28 dias.
    db_conn.execute(
        """
        INSERT INTO indicator_values (id, indicator_id, reference_date, value)
        VALUES ('v-1', 'mon-1', '2025-03-01', 0.4)
        """
    )
    db_conn.commit()
    assert scheduler.should_collect(indicator, conn=db_conn, now=now) is False

    far_future = now + timedelta(days=30)
    assert (
        scheduler.should_collect(indicator, conn=db_conn, now=far_future) is True
    )


# ---------------------------------------------------------------------------
# collect_single / backfill_indicator / run_all
# ---------------------------------------------------------------------------


SERIES_ID = 433
SERIES_URL = BCB_BASE_URL.format(series_id=SERIES_ID)


def _seed_indicator(conn, *, code="X1", series_id=SERIES_ID, indicator_id=None):
    """Insere um indicador de teste limpo (sem colisão com os seeds da Fase 1).

    Apaga eventual indicador com o mesmo `code` para tornar a fixture robusta
    a re-execuções dentro do mesmo banco.
    """
    indicator_id = indicator_id or f"id-{code}"
    conn.execute("DELETE FROM indicators WHERE code = ?", (code,))
    conn.execute(
        """
        INSERT INTO indicators (
            id, code, slug, name, short_description, long_description,
            category, unit, frequency, source_name, source_url,
            connector_type, connector_config, inception_date, active,
            meta_title, meta_description, expected_release_day
        ) VALUES (?, ?, ?, ?, '.', '.', 'inflacao', 'percent', 'monthly',
                  'src', 'http://x', 'bcb_sgs', ?, '2024-01-01', 1, 't', 'd', 10)
        """,
        (indicator_id, code, code.lower(), code, f'{{"series_id": {series_id}}}'),
    )
    conn.commit()
    return get_indicator_by_code(conn, code)


@respx.mock
def test_collect_single_persists_and_recomputes_aggregations(db_conn):
    indicator = _seed_indicator(db_conn)
    payload = [
        {"data": "01/01/2024", "valor": "0.50"},
        {"data": "01/02/2024", "valor": "0.30"},
        {"data": "01/03/2024", "valor": "0.40"},
    ]
    respx.get(SERIES_URL).mock(return_value=httpx.Response(200, json=payload))

    result = scheduler.collect_single(db_conn, indicator, triggered_by="cli")

    assert result.ok
    assert result.added == 3
    assert result.updated == 0

    rows = list_values(db_conn, indicator.id)
    assert len(rows) == 3
    # Agregações foram computadas (ytd não-nulo a partir do primeiro mês).
    assert all(r.ytd is not None for r in rows)
    assert rows[-1].since_inception == pytest.approx(((1.005 * 1.003 * 1.004) - 1) * 100)

    refreshed = get_indicator_by_code(db_conn, "X1")
    assert refreshed.last_collected_at is not None

    log_rows = fetch_all(db_conn, "SELECT status, records_added FROM collection_logs")
    assert len(log_rows) == 1
    assert log_rows[0]["status"] == "success"
    assert log_rows[0]["records_added"] == 3


@respx.mock
def test_collect_single_idempotent_second_run(db_conn):
    indicator = _seed_indicator(db_conn)
    payload = [{"data": "01/01/2024", "valor": "0.50"}]
    respx.get(SERIES_URL).mock(return_value=httpx.Response(200, json=payload))

    first = scheduler.collect_single(db_conn, indicator, triggered_by="cli")
    assert first.added == 1

    # Segunda execução: get_last_value_date avança o `since`, e o BCB devolve nada novo.
    respx.get(SERIES_URL).mock(return_value=httpx.Response(200, json=[]))
    refreshed = get_indicator_by_code(db_conn, "X1")
    second = scheduler.collect_single(db_conn, refreshed, triggered_by="cli")
    assert second.added == 0
    assert second.updated == 0
    assert second.ok


@respx.mock
def test_collect_single_handles_fetch_error(db_conn):
    indicator = _seed_indicator(db_conn)
    respx.get(SERIES_URL).mock(return_value=httpx.Response(500, text="boom"))

    result = scheduler.collect_single(db_conn, indicator, triggered_by="cli")

    assert not result.ok
    assert "FetchError" in (result.error or "")
    refreshed = get_indicator_by_code(db_conn, "X1")
    assert refreshed.last_collected_at is None  # não atualizou em caso de erro

    log_rows = fetch_all(db_conn, "SELECT status, error_message FROM collection_logs")
    assert log_rows[0]["status"] == "error"
    assert log_rows[0]["error_message"]


@respx.mock
def test_run_all_skips_recently_collected(db_conn):
    # Limpa os indicadores semeados pelas migrations para isolar o teste.
    db_conn.execute("DELETE FROM indicators")
    db_conn.commit()

    fresh = _seed_indicator(db_conn, code="A", series_id=111, indicator_id="A-1")
    stale = _seed_indicator(db_conn, code="B", series_id=222, indicator_id="B-1")

    # `fresh` foi coletado há 1 hora → should_collect=False (monthly < 24h).
    db_conn.execute(
        "UPDATE indicators SET last_collected_at = ? WHERE id = ?",
        (
            (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat(),
            fresh.id,
        ),
    )
    db_conn.commit()

    respx.get(BCB_BASE_URL.format(series_id=222)).mock(
        return_value=httpx.Response(
            200, json=[{"data": "01/01/2024", "valor": "0.10"}]
        )
    )

    results = scheduler.run_all(db_conn, triggered_by="cron")

    # Apenas B foi coletado. A virou skipped (não aparece em results).
    codes = [r.code for r in results]
    assert codes == ["B"]

    log_rows = fetch_all(
        db_conn,
        "SELECT indicator_id, status FROM collection_logs ORDER BY started_at",
    )
    statuses = {(r["indicator_id"], r["status"]) for r in log_rows}
    assert (fresh.id, "skipped") in statuses
    assert (stale.id, "success") in statuses


@respx.mock
def test_backfill_calls_connector_with_no_since(db_conn):
    indicator = _seed_indicator(db_conn)
    calls: list[dict[str, str]] = []

    def _record(request):
        calls.append(dict(request.url.params))
        return httpx.Response(200, json=[{"data": "01/01/2024", "valor": "0.30"}])

    respx.get(SERIES_URL).mock(side_effect=_record)

    result = scheduler.backfill_indicator(db_conn, indicator, triggered_by="backfill")

    assert result.ok
    # since=None aciona o default do conector (1986-01-01) na primeira janela.
    assert calls, "esperava ao menos uma chamada HTTP"
    assert calls[0]["dataInicial"].endswith("/1986")

    log_rows = fetch_all(db_conn, "SELECT triggered_by FROM collection_logs")
    assert log_rows[-1]["triggered_by"] == "backfill"
