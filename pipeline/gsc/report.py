"""Briefing semanal derivado das tabelas gsc_*_daily."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta

from pipeline.db.connection import fetch_all, fetch_one
from pipeline.gsc.persist import list_indicator_slugs
from pipeline.gsc.urls import (
    is_asset_path,
    is_index_html,
    is_published_path,
    is_www,
)

OURO_MIN_IMPRESSIONS = 10
OURO_POSITION_MIN = 15.0
OURO_POSITION_MAX = 70.0
SNIPPET_MAX_POSITION = 10.0
SNIPPET_MAX_CTR = 0.02
SNIPPET_MIN_IMPRESSIONS = 10
STRIKING_MIN = 8.0
STRIKING_MAX = 20.0
LIST_LIMIT = 8
NEW_QUERY_LOOKBACK_DAYS = 28


@dataclass(frozen=True)
class QueryStat:
    query: str
    clicks: float
    impressions: float
    ctr: float
    position: float
    page: str | None = None
    canonical_path: str | None = None


@dataclass(frozen=True)
class Totals:
    clicks: float
    impressions: float
    ctr: float
    position: float


@dataclass
class GscBriefing:
    window_start: date
    window_end: date
    current: Totals
    previous: Totals
    ouro: list[QueryStat] = field(default_factory=list)
    snippet: list[QueryStat] = field(default_factory=list)
    striking: list[QueryStat] = field(default_factory=list)
    new_queries: list[QueryStat] = field(default_factory=list)
    gaps: list[QueryStat] = field(default_factory=list)
    hygiene_www: int = 0
    hygiene_index_html: int = 0
    hygiene_png: int = 0
    appearance_labels: list[str] = field(default_factory=list)


_AGG_SQL = """
SELECT
    query,
    SUM(clicks) AS clicks,
    SUM(impressions) AS impressions,
    CASE WHEN SUM(impressions) > 0
         THEN SUM(clicks) * 1.0 / SUM(impressions) ELSE 0 END AS ctr,
    CASE WHEN SUM(impressions) > 0
         THEN SUM(position * impressions) / SUM(impressions) ELSE 0 END AS position
  FROM gsc_query_daily
 WHERE date >= ? AND date <= ?
 GROUP BY query
"""


def _totals_from_stats(stats: list[QueryStat]) -> Totals:
    clicks = sum(s.clicks for s in stats)
    impressions = sum(s.impressions for s in stats)
    ctr = (clicks / impressions) if impressions else 0.0
    if impressions:
        position = sum(s.position * s.impressions for s in stats) / impressions
    else:
        position = 0.0
    return Totals(clicks=clicks, ctr=ctr, impressions=impressions, position=position)


def _query_stats(
    conn: sqlite3.Connection, start: date, end: date
) -> list[QueryStat]:
    rows = fetch_all(conn, _AGG_SQL, (start.isoformat(), end.isoformat()))
    return [
        QueryStat(
            clicks=float(row["clicks"] or 0),
            ctr=float(row["ctr"] or 0),
            impressions=float(row["impressions"] or 0),
            position=float(row["position"] or 0),
            query=row["query"],
        )
        for row in rows
    ]


def _top_landing_by_query(
    conn: sqlite3.Connection, start: date, end: date
) -> dict[str, QueryStat]:
    rows = fetch_all(
        conn,
        """
        SELECT query, page, canonical_path,
               SUM(clicks) AS clicks,
               SUM(impressions) AS impressions
          FROM gsc_query_page_daily
         WHERE date >= ? AND date <= ?
         GROUP BY query, page, canonical_path
        """,
        (start.isoformat(), end.isoformat()),
    )
    best: dict[str, QueryStat] = {}
    for row in rows:
        query = row["query"]
        impressions = float(row["impressions"] or 0)
        current = best.get(query)
        if current is None or impressions > current.impressions:
            best[query] = QueryStat(
                canonical_path=row["canonical_path"],
                clicks=float(row["clicks"] or 0),
                ctr=0.0,
                impressions=impressions,
                page=row["page"],
                position=0.0,
                query=query,
            )
    return best


def _hygiene_counts(
    conn: sqlite3.Connection, start: date, end: date
) -> tuple[int, int, int]:
    rows = fetch_all(
        conn,
        """
        SELECT DISTINCT page
          FROM gsc_page_daily
         WHERE date >= ? AND date <= ?
        """,
        (start.isoformat(), end.isoformat()),
    )
    www = index_html = png = 0
    for row in rows:
        page = row["page"]
        if is_www(page):
            www += 1
        if is_index_html(page):
            index_html += 1
        if is_asset_path(page):
            png += 1
    return www, index_html, png


def _appearance_labels(
    conn: sqlite3.Connection, start: date, end: date
) -> list[str]:
    rows = fetch_all(
        conn,
        """
        SELECT DISTINCT search_appearance
          FROM gsc_appearance_daily
         WHERE date >= ? AND date <= ?
         ORDER BY search_appearance
        """,
        (start.isoformat(), end.isoformat()),
    )
    return [row["search_appearance"] for row in rows]


def window_for(
    conn: sqlite3.Connection,
    *,
    days: int = 7,
    today: date | None = None,
) -> tuple[date, date]:
    today = today or date.today()
    row = fetch_one(conn, "SELECT MAX(date) AS d FROM gsc_query_daily")
    if row is None or row["d"] is None:
        end = today - timedelta(days=2)
    else:
        end = date.fromisoformat(row["d"])
    start = end - timedelta(days=days - 1)
    return start, end


def build_briefing(
    conn: sqlite3.Connection,
    *,
    days: int = 7,
    today: date | None = None,
) -> GscBriefing:
    start, end = window_for(conn, days=days, today=today)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    lookback_start = start - timedelta(days=NEW_QUERY_LOOKBACK_DAYS)

    current_stats = _query_stats(conn, start, end)
    previous_stats = _query_stats(conn, prev_start, prev_end)
    lookback_stats = _query_stats(conn, lookback_start, prev_end)
    lookback_queries = {s.query for s in lookback_stats}

    ouro = [
        s
        for s in current_stats
        if s.impressions >= OURO_MIN_IMPRESSIONS
        and OURO_POSITION_MIN <= s.position <= OURO_POSITION_MAX
    ]
    ouro.sort(key=lambda s: s.impressions, reverse=True)

    snippet = [
        s
        for s in current_stats
        if s.impressions >= SNIPPET_MIN_IMPRESSIONS
        and s.position <= SNIPPET_MAX_POSITION
        and s.ctr <= SNIPPET_MAX_CTR
    ]
    snippet.sort(key=lambda s: s.impressions, reverse=True)

    striking = [
        s
        for s in current_stats
        if STRIKING_MIN <= s.position <= STRIKING_MAX
    ]
    striking.sort(key=lambda s: s.impressions, reverse=True)

    new_queries = [s for s in current_stats if s.query not in lookback_queries]
    new_queries.sort(key=lambda s: s.impressions, reverse=True)

    slugs = list_indicator_slugs(conn)
    landings = _top_landing_by_query(conn, start, end)
    stats_by_query = {s.query: s for s in current_stats}
    gaps: list[QueryStat] = []
    for query, landing in landings.items():
        path = landing.canonical_path or "/"
        if is_asset_path(path):
            continue
        if is_published_path(path, slugs):
            continue
        base = stats_by_query.get(query)
        gaps.append(
            QueryStat(
                canonical_path=path,
                clicks=base.clicks if base else landing.clicks,
                ctr=base.ctr if base else 0.0,
                impressions=base.impressions if base else landing.impressions,
                page=landing.page,
                position=base.position if base else 0.0,
                query=query,
            )
        )
    gaps.sort(key=lambda s: s.impressions, reverse=True)

    www, index_html, png = _hygiene_counts(conn, start, end)

    return GscBriefing(
        appearance_labels=_appearance_labels(conn, start, end),
        current=_totals_from_stats(current_stats),
        gaps=gaps[:LIST_LIMIT],
        hygiene_index_html=index_html,
        hygiene_png=png,
        hygiene_www=www,
        new_queries=new_queries[:LIST_LIMIT],
        ouro=ouro[:LIST_LIMIT],
        previous=_totals_from_stats(previous_stats),
        snippet=snippet[:LIST_LIMIT],
        striking=striking[:LIST_LIMIT],
        window_end=end,
        window_start=start,
    )
