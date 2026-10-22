from __future__ import annotations

from datetime import date

from pipeline.gsc.client import GscRow
from pipeline.gsc.persist import upsert_page_daily, upsert_query_daily, upsert_query_page_daily
from pipeline.gsc.report import build_briefing


def test_briefing_classifies_ouro_snippet_striking_new_and_gap(db_conn):
    window_day = date(2026, 9, 10)
    prev_day = date(2026, 8, 20)

    upsert_query_daily(
        db_conn,
        window_day,
        [
            GscRow(keys=("cdi hoje",), clicks=0, impressions=50, ctr=0, position=40.0),
            GscRow(keys=("tr tabela",), clicks=0, impressions=20, ctr=0, position=9.0),
            GscRow(keys=("incc 10 anos",), clicks=1, impressions=30, ctr=0.03, position=12.0),
            GscRow(keys=("pib tabela historica",), clicks=0, impressions=15, ctr=0, position=25.0),
        ],
    )
    upsert_query_daily(
        db_conn,
        prev_day,
        [
            GscRow(keys=("tr tabela",), clicks=0, impressions=10, ctr=0, position=9.0),
        ],
    )
    upsert_query_page_daily(
        db_conn,
        window_day,
        [
            GscRow(
                keys=("pib tabela historica", "https://indicadoreseconomicoshoje.com.br/pib/"),
                clicks=0,
                impressions=15,
                ctr=0,
                position=25.0,
            ),
            GscRow(
                keys=("cdi hoje", "https://indicadoreseconomicoshoje.com.br/cdi/"),
                clicks=0,
                impressions=50,
                ctr=0,
                position=40.0,
            ),
        ],
    )
    upsert_page_daily(
        db_conn,
        window_day,
        [
            GscRow(
                keys=("https://www.indicadoreseconomicoshoje.com.br/inpc/index.html",),
                clicks=0,
                impressions=3,
                ctr=0,
                position=16.0,
            ),
            GscRow(
                keys=("https://indicadoreseconomicoshoje.com.br/cdi/grafico.png",),
                clicks=0,
                impressions=1,
                ctr=0,
                position=25.0,
            ),
        ],
    )

    briefing = build_briefing(db_conn, days=7, today=date(2026, 9, 12))
    assert briefing.window_end == window_day
    ouro_queries = {s.query for s in briefing.ouro}
    assert "cdi hoje" in ouro_queries
    snippet_queries = {s.query for s in briefing.snippet}
    assert "tr tabela" in snippet_queries
    striking_queries = {s.query for s in briefing.striking}
    assert "incc 10 anos" in striking_queries
    new_queries = {s.query for s in briefing.new_queries}
    assert "cdi hoje" in new_queries
    assert "tr tabela" not in new_queries
    gap_queries = {s.query for s in briefing.gaps}
    assert "pib tabela historica" in gap_queries
    assert "cdi hoje" not in gap_queries
    assert briefing.hygiene_www == 1
    assert briefing.hygiene_index_html == 1
    assert briefing.hygiene_png == 1
    assert briefing.current.impressions == 115
