"""Coleta orquestrada — decide o que rodar e dispara conector + persistência.

Spec em docs/05-pipeline.md. Erros de coleta são contidos: registramos no
collection_log e no logger, mas não propagamos para que `run_all` continue
processando os demais indicadores. A integração com o bot Telegram entra no M8.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone

from dateutil.relativedelta import relativedelta

from pipeline.connectors.base import get_connector
from pipeline.core.aggregations import recompute_aggregations
from pipeline.db.connection import (
    Indicator,
    finish_collection_log,
    fetch_one,
    get_last_value_date,
    list_active_indicators,
    record_skipped_collection,
    start_collection_log,
    update_indicator_last_collected_at,
    upsert_value,
)

logger = logging.getLogger(__name__)


@dataclass
class CollectResult:
    code: str
    added: int
    updated: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.fromisoformat(value[:-1]).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value)


def _has_value_for_month(
    conn: sqlite3.Connection, indicator_id: str, target: date
) -> bool:
    row = fetch_one(
        conn,
        """
        SELECT 1 FROM indicator_values
         WHERE indicator_id = ?
           AND substr(reference_date, 1, 7) = ?
         LIMIT 1
        """,
        (indicator_id, target.strftime("%Y-%m")),
    )
    return row is not None


def should_collect(
    indicator: Indicator,
    *,
    conn: sqlite3.Connection | None = None,
    now: datetime | None = None,
) -> bool:
    """Replica a regra documentada em docs/05-pipeline.md.

    `conn` só é necessário para indicadores `monthly` (consulta valor do mês
    anterior). Para `daily`/`biweekly` o argumento é ignorado.
    """
    now = now or datetime.now(tz=timezone.utc)
    if indicator.last_collected_at is None:
        return True

    last = _parse_iso_datetime(indicator.last_collected_at)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    elapsed_hours = (now - last).total_seconds() / 3600

    freq = indicator.frequency
    if freq == "daily":
        return elapsed_hours >= 20
    if freq == "biweekly":
        return elapsed_hours >= 24 * 14
    if freq == "monthly":
        if elapsed_hours < 24:
            return False
        if conn is None:
            return True
        last_month_anchor = (now.date().replace(day=1) - relativedelta(months=1))
        if _has_value_for_month(conn, indicator.id, last_month_anchor):
            return elapsed_hours >= 24 * 28
        return True
    raise ValueError(f"Frequência desconhecida: {freq}")


def _next_since(
    conn: sqlite3.Connection, indicator: Indicator
) -> date | None:
    last = get_last_value_date(conn, indicator.id)
    if last is None:
        return None
    return last + relativedelta(months=1)


def _run_collection(
    conn: sqlite3.Connection,
    indicator: Indicator,
    triggered_by: str,
    *,
    since: date | None,
) -> CollectResult:
    log_id = start_collection_log(conn, indicator.id, triggered_by)
    try:
        connector = get_connector(indicator.connector_type)
        config = json.loads(indicator.connector_config)
        points = connector.fetch(config, since=since)

        added = 0
        updated = 0
        for point in points:
            existed = upsert_value(conn, indicator.id, point)
            if existed:
                updated += 1
            else:
                added += 1

        if added or updated:
            recompute_aggregations(conn, indicator.id)
            update_indicator_last_collected_at(
                conn,
                indicator.id,
                datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

        finish_collection_log(
            conn, log_id, status="success", added=added, updated=updated
        )
        logger.info(
            "collect %s ok: added=%d updated=%d (since=%s)",
            indicator.code,
            added,
            updated,
            since,
        )
        return CollectResult(code=indicator.code, added=added, updated=updated)
    except Exception as exc:  # noqa: BLE001 — fail-loud, mas não derruba o batch
        message = f"{type(exc).__name__}: {exc}"
        finish_collection_log(
            conn, log_id, status="error", error_message=message
        )
        logger.warning("collect %s falhou: %s", indicator.code, message)
        try:
            from pipeline.bot import notifications

            notifications.send_collect_error(indicator, message)
        except Exception:  # noqa: BLE001 — notificação nunca derruba pipeline
            logger.exception("Falha ao notificar erro de coleta")
        return CollectResult(
            code=indicator.code, added=0, updated=0, error=message
        )


def collect_single(
    conn: sqlite3.Connection,
    indicator: Indicator,
    triggered_by: str = "cli",
) -> CollectResult:
    return _run_collection(
        conn, indicator, triggered_by, since=_next_since(conn, indicator)
    )


def backfill_indicator(
    conn: sqlite3.Connection,
    indicator: Indicator,
    triggered_by: str = "backfill",
) -> CollectResult:
    # Usa inception_date para não varrer janelas vazias pré-série (ex.: SGS
    # diária desde 2012 que timeoutava em 1986–1995).
    return _run_collection(
        conn, indicator, triggered_by, since=indicator.inception_date
    )


def run_all(
    conn: sqlite3.Connection, triggered_by: str = "cron"
) -> list[CollectResult]:
    # Atualiza datas oficiais de divulgação (IBGE) — fail-soft, nunca derruba.
    try:
        from pipeline.core import release_calendar

        release_calendar.refresh_official_dates(conn)
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao atualizar calendário de divulgação")

    results: list[CollectResult] = []
    for indicator in list_active_indicators(conn):
        if not should_collect(indicator, conn=conn):
            record_skipped_collection(conn, indicator.id, triggered_by)
            logger.info("skip %s (should_collect=False)", indicator.code)
            continue
        results.append(collect_single(conn, indicator, triggered_by))

    if results and triggered_by != "telegram":
        try:
            from pipeline.bot import notifications

            notifications.send_collect_success(results)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao notificar resumo de coleta")
    return results
