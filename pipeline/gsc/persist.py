"""Upserts idempotentes das tabelas gsc_* no SQLite."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone

from pipeline.db.connection import execute, fetch_all, fetch_one
from pipeline.gsc.client import GscRow
from pipeline.gsc.urls import canonical_path

_QUERY_UPSERT = """
INSERT INTO gsc_query_daily (date, query, clicks, impressions, ctr, position)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(date, query) DO UPDATE SET
    clicks      = excluded.clicks,
    impressions = excluded.impressions,
    ctr         = excluded.ctr,
    position    = excluded.position
"""

_PAGE_UPSERT = """
INSERT INTO gsc_page_daily
    (date, page, canonical_path, clicks, impressions, ctr, position)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(date, page) DO UPDATE SET
    canonical_path = excluded.canonical_path,
    clicks         = excluded.clicks,
    impressions    = excluded.impressions,
    ctr            = excluded.ctr,
    position       = excluded.position
"""

_QUERY_PAGE_UPSERT = """
INSERT INTO gsc_query_page_daily
    (date, query, page, canonical_path, clicks, impressions, ctr, position)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(date, query, page) DO UPDATE SET
    canonical_path = excluded.canonical_path,
    clicks         = excluded.clicks,
    impressions    = excluded.impressions,
    ctr            = excluded.ctr,
    position       = excluded.position
"""

_APPEARANCE_UPSERT = """
INSERT INTO gsc_appearance_daily
    (date, search_appearance, clicks, impressions, ctr, position)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(date, search_appearance) DO UPDATE SET
    clicks      = excluded.clicks,
    impressions = excluded.impressions,
    ctr         = excluded.ctr,
    position    = excluded.position
"""


def latest_stored_date(conn: sqlite3.Connection) -> date | None:
    row = fetch_one(conn, "SELECT MAX(date) AS d FROM gsc_query_daily")
    if row is None or row["d"] is None:
        return None
    return date.fromisoformat(row["d"])


def list_indicator_slugs(conn: sqlite3.Connection) -> set[str]:
    rows = fetch_all(conn, "SELECT slug FROM indicators")
    return {row["slug"] for row in rows}


def upsert_query_daily(
    conn: sqlite3.Connection, day: date, rows: list[GscRow]
) -> int:
    day_s = day.isoformat()
    params = [
        (
            day_s,
            row.keys[0] if row.keys else "",
            row.clicks,
            row.impressions,
            row.ctr,
            row.position,
        )
        for row in rows
        if row.keys
    ]
    if not params:
        return 0
    with conn:
        conn.executemany(_QUERY_UPSERT, params)
    return len(params)


def upsert_page_daily(
    conn: sqlite3.Connection, day: date, rows: list[GscRow]
) -> int:
    day_s = day.isoformat()
    params = []
    for row in rows:
        if not row.keys:
            continue
        page = row.keys[0]
        params.append(
            (
                day_s,
                page,
                canonical_path(page),
                row.clicks,
                row.impressions,
                row.ctr,
                row.position,
            )
        )
    if not params:
        return 0
    with conn:
        conn.executemany(_PAGE_UPSERT, params)
    return len(params)


def upsert_query_page_daily(
    conn: sqlite3.Connection, day: date, rows: list[GscRow]
) -> int:
    day_s = day.isoformat()
    params = []
    for row in rows:
        if len(row.keys) < 2:
            continue
        query, page = row.keys[0], row.keys[1]
        params.append(
            (
                day_s,
                query,
                page,
                canonical_path(page),
                row.clicks,
                row.impressions,
                row.ctr,
                row.position,
            )
        )
    if not params:
        return 0
    with conn:
        conn.executemany(_QUERY_PAGE_UPSERT, params)
    return len(params)


def upsert_appearance_daily(
    conn: sqlite3.Connection, day: date, rows: list[GscRow]
) -> int:
    day_s = day.isoformat()
    params = [
        (
            day_s,
            row.keys[0] if row.keys else "",
            row.clicks,
            row.impressions,
            row.ctr,
            row.position,
        )
        for row in rows
        if row.keys
    ]
    if not params:
        return 0
    with conn:
        conn.executemany(_APPEARANCE_UPSERT, params)
    return len(params)


def start_sync_log(
    conn: sqlite3.Connection,
    *,
    triggered_by: str,
    data_state: str,
    start: date | None,
    end: date | None,
) -> str:
    log_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    execute(
        conn,
        """
        INSERT INTO gsc_sync_log (
            id, triggered_by, started_at, status, data_state,
            start_date, end_date
        ) VALUES (?, ?, ?, 'running', ?, ?, ?)
        """,
        (
            log_id,
            triggered_by,
            now,
            data_state,
            start.isoformat() if start else None,
            end.isoformat() if end else None,
        ),
    )
    conn.commit()
    return log_id


def finish_sync_log(
    conn: sqlite3.Connection,
    log_id: str,
    *,
    status: str,
    days_ok: int = 0,
    rows_upserted: int = 0,
    error_message: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> None:
    now = datetime.now(tz=timezone.utc).isoformat()
    execute(
        conn,
        """
        UPDATE gsc_sync_log
           SET finished_at   = ?,
               status        = ?,
               days_ok       = ?,
               rows_upserted = ?,
               error_message = ?,
               start_date    = COALESCE(?, start_date),
               end_date      = COALESCE(?, end_date)
         WHERE id = ?
        """,
        (
            now,
            status,
            days_ok,
            rows_upserted,
            error_message,
            start.isoformat() if start else None,
            end.isoformat() if end else None,
            log_id,
        ),
    )
    conn.commit()
