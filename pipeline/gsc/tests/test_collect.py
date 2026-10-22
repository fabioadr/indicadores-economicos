from __future__ import annotations

from datetime import date

from pipeline.gsc.client import GscRow
from pipeline.gsc.collect import collect, resolve_range
from pipeline.gsc.exceptions import GscFetchError
from pipeline.gsc.persist import latest_stored_date


class FakeClient:
    data_state = "final"

    def __init__(self, *, fail_appearance: bool = False) -> None:
        self.fail_appearance = fail_appearance
        self.dimensions_seen: list[tuple[str, ...]] = []

    def available_dates(self, start: date, end: date) -> list[date]:
        return [end]

    def query(self, start: date, end: date, dimensions, **kwargs):
        dim = tuple(dimensions)
        self.dimensions_seen.append(dim)
        if dim == ("searchAppearance",) and self.fail_appearance:
            raise GscFetchError("searchAppearance 400")
        if dim == ("query",):
            return [
                GscRow(
                    clicks=0,
                    ctr=0,
                    impressions=10,
                    keys=("cdi hoje",),
                    position=40.0,
                )
            ]
        if dim == ("page",):
            return [
                GscRow(
                    clicks=0,
                    ctr=0,
                    impressions=10,
                    keys=("https://indicadoreseconomicoshoje.com.br/cdi/",),
                    position=22.0,
                )
            ]
        if dim == ("query", "page"):
            return [
                GscRow(
                    clicks=0,
                    ctr=0,
                    impressions=10,
                    keys=(
                        "cdi hoje",
                        "https://indicadoreseconomicoshoje.com.br/cdi/",
                    ),
                    position=40.0,
                )
            ]
        if dim == ("searchAppearance",):
            return [
                GscRow(
                    clicks=0,
                    ctr=0,
                    impressions=1,
                    keys=("AI_OVERVIEW",),
                    position=1.0,
                )
            ]
        return []


def test_resolve_range_incremental_when_empty(db_conn):
    start, end = resolve_range(
        db_conn,
        backfill=False,
        since=None,
        today=date(2026, 9, 12),
        until=None,
    )
    assert end == date(2026, 9, 10)
    assert (end - start).days == 6


def test_resolve_range_backfill_is_sixteen_months(db_conn):
    start, end = resolve_range(
        db_conn,
        backfill=True,
        since=None,
        today=date(2026, 9, 12),
        until=None,
    )
    assert end == date(2026, 9, 10)
    assert start < date(2025, 6, 1)


def test_collect_upserts_and_is_idempotent(db_conn, monkeypatch):
    monkeypatch.setattr("pipeline.gsc.collect.INTER_DAY_PAUSE_SECONDS", 0)
    client = FakeClient()
    first = collect(
        db_conn,
        client,
        since=date(2026, 9, 10),
        today=date(2026, 9, 12),
        until=date(2026, 9, 10),
    )
    assert first.ok
    assert first.days_ok == 1
    assert first.rows_upserted > 0
    assert first.appearance_rows == 1
    assert latest_stored_date(db_conn) == date(2026, 9, 10)

    second = collect(
        db_conn,
        client,
        since=date(2026, 9, 10),
        until=date(2026, 9, 10),
    )
    assert second.ok
    assert second.rows_upserted == first.rows_upserted


def test_collect_appearance_fail_soft(db_conn, monkeypatch):
    monkeypatch.setattr("pipeline.gsc.collect.INTER_DAY_PAUSE_SECONDS", 0)
    client = FakeClient(fail_appearance=True)
    result = collect(
        db_conn,
        client,
        since=date(2026, 9, 10),
        until=date(2026, 9, 10),
    )
    assert result.ok
    assert result.appearance_rows == 0
    assert latest_stored_date(db_conn) == date(2026, 9, 10)
