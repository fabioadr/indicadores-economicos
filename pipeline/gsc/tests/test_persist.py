from __future__ import annotations

from datetime import date

from pipeline.db.connection import fetch_one
from pipeline.gsc.client import GscRow
from pipeline.gsc.persist import (
    latest_stored_date,
    upsert_appearance_daily,
    upsert_page_daily,
    upsert_query_daily,
    upsert_query_page_daily,
)


def test_query_upsert_is_idempotent(db_conn):
    day = date(2026, 9, 1)
    rows = [
        GscRow(
            clicks=1,
            ctr=0.1,
            impressions=10,
            keys=("cdi hoje",),
            position=40.0,
        )
    ]
    assert upsert_query_daily(db_conn, day, rows) == 1
    rows[0] = GscRow(
        clicks=2,
        ctr=0.2,
        impressions=20,
        keys=("cdi hoje",),
        position=30.0,
    )
    upsert_query_daily(db_conn, day, rows)
    stored = fetch_one(
        db_conn,
        "SELECT clicks, impressions, position FROM gsc_query_daily",
    )
    assert stored["clicks"] == 2
    assert stored["impressions"] == 20
    assert stored["position"] == 30.0
    assert latest_stored_date(db_conn) == day


def test_page_stores_canonical_path(db_conn):
    day = date(2026, 9, 1)
    url = "https://www.indicadoreseconomicoshoje.com.br/cdi/index.html"
    upsert_page_daily(
        db_conn,
        day,
        [
            GscRow(
                clicks=0,
                ctr=0,
                impressions=5,
                keys=(url,),
                position=12.0,
            )
        ],
    )
    row = fetch_one(db_conn, "SELECT canonical_path FROM gsc_page_daily")
    assert row["canonical_path"] == "/cdi/"


def test_query_page_and_appearance(db_conn):
    day = date(2026, 9, 2)
    upsert_query_page_daily(
        db_conn,
        day,
        [
            GscRow(
                clicks=0,
                ctr=0,
                impressions=8,
                keys=("cdi hoje", "https://indicadoreseconomicoshoje.com.br/cdi/"),
                position=20.0,
            )
        ],
    )
    upsert_appearance_daily(
        db_conn,
        day,
        [
            GscRow(
                clicks=0,
                ctr=0,
                impressions=3,
                keys=("AMP_BLUE_LINK",),
                position=5.0,
            )
        ],
    )
    qp = fetch_one(db_conn, "SELECT canonical_path FROM gsc_query_page_daily")
    app = fetch_one(db_conn, "SELECT search_appearance FROM gsc_appearance_daily")
    assert qp["canonical_path"] == "/cdi/"
    assert app["search_appearance"] == "AMP_BLUE_LINK"
