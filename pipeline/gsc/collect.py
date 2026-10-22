"""Coleta dia a dia da Search Console API → SQLite."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from pipeline.gsc.client import GscClient
from pipeline.gsc.exceptions import GscError, GscFetchError
from pipeline.gsc.persist import (
    finish_sync_log,
    latest_stored_date,
    start_sync_log,
    upsert_appearance_daily,
    upsert_page_daily,
    upsert_query_daily,
    upsert_query_page_daily,
)

logger = logging.getLogger(__name__)

INTER_DAY_PAUSE_SECONDS = 0.05
INCREMENTAL_DAYS = 7
REWRITE_OVERLAP_DAYS = 3
DATA_LAG_DAYS = 2
BACKFILL_MONTHS = 16


@dataclass
class GscCollectResult:
    start: date | None
    end: date | None
    days_ok: int
    days_empty: int
    rows_upserted: int
    appearance_rows: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def resolve_range(
    conn: sqlite3.Connection,
    *,
    backfill: bool,
    since: date | None,
    until: date | None,
    today: date | None = None,
) -> tuple[date, date]:
    today = today or date.today()
    end = until or (today - timedelta(days=DATA_LAG_DAYS))
    if since is not None:
        return since, end
    if backfill:
        start = end - relativedelta(months=BACKFILL_MONTHS) + timedelta(days=1)
        return start, end
    last = latest_stored_date(conn)
    if last is None:
        return end - timedelta(days=INCREMENTAL_DAYS - 1), end
    start = min(last - timedelta(days=REWRITE_OVERLAP_DAYS), end - timedelta(days=INCREMENTAL_DAYS - 1))
    return start, end


def _iter_days(start: date, end: date):
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def collect(
    conn: sqlite3.Connection,
    client: GscClient,
    *,
    triggered_by: str = "cli",
    backfill: bool = False,
    since: date | None = None,
    until: date | None = None,
    today: date | None = None,
) -> GscCollectResult:
    log_id = start_sync_log(
        conn,
        data_state=client.data_state,
        end=until,
        start=since,
        triggered_by=triggered_by,
    )
    try:
        start, end = resolve_range(
            conn,
            backfill=backfill,
            since=since,
            today=today,
            until=until,
        )
        if start > end:
            result = GscCollectResult(
                appearance_rows=0,
                days_empty=0,
                days_ok=0,
                end=end,
                rows_upserted=0,
                start=start,
            )
            finish_sync_log(
                conn,
                log_id,
                days_ok=0,
                end=end,
                rows_upserted=0,
                start=start,
                status="success",
            )
            return result

        probe_end = end
        probe_start = max(start, end - timedelta(days=9))
        try:
            available = client.available_dates(probe_start, probe_end)
        except GscFetchError as exc:
            logger.warning("GSC available_dates falhou (%s); segue com até %s", exc, end)
            available = []
        if available:
            end = min(end, available[-1])
            if start > end:
                result = GscCollectResult(
                    appearance_rows=0,
                    days_empty=0,
                    days_ok=0,
                    end=end,
                    rows_upserted=0,
                    start=start,
                )
                finish_sync_log(
                    conn,
                    log_id,
                    days_ok=0,
                    end=end,
                    rows_upserted=0,
                    start=start,
                    status="success",
                )
                return result

        days_ok = 0
        days_empty = 0
        rows_upserted = 0
        appearance_rows = 0
        days = list(_iter_days(start, end))
        for i, day in enumerate(days):
            q_rows = client.query(day, day, ("query",))
            p_rows = client.query(day, day, ("page",))
            qp_rows = client.query(day, day, ("query", "page"))
            added = 0
            added += upsert_query_daily(conn, day, q_rows)
            added += upsert_page_daily(conn, day, p_rows)
            added += upsert_query_page_daily(conn, day, qp_rows)
            try:
                a_rows = client.query(day, day, ("searchAppearance",))
                appearance_rows += upsert_appearance_daily(conn, day, a_rows)
            except GscError as exc:
                logger.warning(
                    "GSC searchAppearance indisponível em %s: %s",
                    day.isoformat(),
                    exc,
                )
            rows_upserted += added
            if added:
                days_ok += 1
            else:
                days_empty += 1
            if i < len(days) - 1 and INTER_DAY_PAUSE_SECONDS:
                time.sleep(INTER_DAY_PAUSE_SECONDS)

        result = GscCollectResult(
            appearance_rows=appearance_rows,
            days_empty=days_empty,
            days_ok=days_ok,
            end=end,
            rows_upserted=rows_upserted,
            start=start,
        )
        finish_sync_log(
            conn,
            log_id,
            days_ok=days_ok,
            end=end,
            rows_upserted=rows_upserted,
            start=start,
            status="success",
        )
        return result
    except Exception as exc:
        finish_sync_log(
            conn,
            log_id,
            error_message=str(exc),
            status="error",
        )
        return GscCollectResult(
            appearance_rows=0,
            days_empty=0,
            days_ok=0,
            end=until,
            error=str(exc),
            rows_upserted=0,
            start=since,
        )
