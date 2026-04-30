"""SQLite connection helpers, migration runner, and domain accessors.

M1 brought connection/migration plumbing; M3 added value persistence and
aggregation helpers; M4 layers on indicator lookups and `collection_logs`
helpers used by the scheduler.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.connectors.base import RawDataPoint

_MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _migrations (
    name        TEXT PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(
    conn: sqlite3.Connection,
    sql: str,
    params: Iterable = (),
) -> sqlite3.Cursor:
    return conn.execute(sql, tuple(params))


def fetch_one(
    conn: sqlite3.Connection,
    sql: str,
    params: Iterable = (),
) -> sqlite3.Row | None:
    return conn.execute(sql, tuple(params)).fetchone()


def fetch_all(
    conn: sqlite3.Connection,
    sql: str,
    params: Iterable = (),
) -> list[sqlite3.Row]:
    return conn.execute(sql, tuple(params)).fetchall()


def executescript(conn: sqlite3.Connection, sql: str) -> None:
    conn.executescript(sql)


@dataclass
class IndicatorValue:
    id: str
    indicator_id: str
    reference_date: date
    value: float
    ytd: float | None
    last_12m: float | None
    last_24m: float | None
    since_inception: float | None
    raw_value: str | None


def upsert_value(
    conn: sqlite3.Connection,
    indicator_id: str,
    point: RawDataPoint,
) -> bool:
    """Insert or update a value for `(indicator_id, reference_date)`.

    Returns True when a row already existed (i.e. the call was an update),
    False when a new row was inserted.
    """
    ref = point.reference_date.isoformat()
    existing = fetch_one(
        conn,
        "SELECT id FROM indicator_values WHERE indicator_id = ? AND reference_date = ?",
        (indicator_id, ref),
    )
    with conn:
        if existing is None:
            conn.execute(
                """
                INSERT INTO indicator_values (
                    id, indicator_id, reference_date, value, raw_value
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), indicator_id, ref, point.value, point.raw_value),
            )
            return False
        conn.execute(
            """
            UPDATE indicator_values
               SET value        = ?,
                   raw_value    = ?,
                   collected_at = datetime('now')
             WHERE id = ?
            """,
            (point.value, point.raw_value, existing["id"]),
        )
        return True


def list_values(
    conn: sqlite3.Connection,
    indicator_id: str,
    order: str = "asc",
) -> list[IndicatorValue]:
    direction = "ASC" if order.lower() == "asc" else "DESC"
    rows = fetch_all(
        conn,
        f"""
        SELECT id, indicator_id, reference_date, value,
               ytd, last_12m, last_24m, since_inception, raw_value
          FROM indicator_values
         WHERE indicator_id = ?
         ORDER BY reference_date {direction}
        """,
        (indicator_id,),
    )
    return [
        IndicatorValue(
            id=row["id"],
            indicator_id=row["indicator_id"],
            reference_date=date.fromisoformat(row["reference_date"]),
            value=row["value"],
            ytd=row["ytd"],
            last_12m=row["last_12m"],
            last_24m=row["last_24m"],
            since_inception=row["since_inception"],
            raw_value=row["raw_value"],
        )
        for row in rows
    ]


def get_last_value_date(
    conn: sqlite3.Connection,
    indicator_id: str,
) -> date | None:
    row = fetch_one(
        conn,
        "SELECT MAX(reference_date) AS d FROM indicator_values WHERE indicator_id = ?",
        (indicator_id,),
    )
    if row is None or row["d"] is None:
        return None
    return date.fromisoformat(row["d"])


def batch_update_aggregations(
    conn: sqlite3.Connection,
    updates: list[tuple[str, float | None, float | None, float | None, float]],
) -> None:
    """Apply ytd / last_12m / last_24m / since_inception updates in one tx.

    Each tuple is `(id, ytd, last_12m, last_24m, since_inception)`.
    """
    if not updates:
        return
    payload = [(ytd, l12, l24, si, vid) for (vid, ytd, l12, l24, si) in updates]
    with conn:
        conn.executemany(
            """
            UPDATE indicator_values
               SET ytd             = ?,
                   last_12m        = ?,
                   last_24m        = ?,
                   since_inception = ?
             WHERE id = ?
            """,
            payload,
        )


@dataclass
class Indicator:
    id: str
    code: str
    slug: str
    name: str
    category: str
    frequency: str
    connector_type: str
    connector_config: str
    inception_date: date
    expected_release_day: int | None
    active: bool
    last_collected_at: str | None
    short_description: str = ""
    long_description: str = ""
    unit: str = "percent"
    source_name: str = ""
    source_url: str = ""
    meta_title: str = ""
    meta_description: str = ""
    last_built_at: str | None = None


_INDICATOR_COLUMNS = (
    "id, code, slug, name, category, frequency, "
    "connector_type, connector_config, inception_date, "
    "expected_release_day, active, last_collected_at, "
    "short_description, long_description, unit, "
    "source_name, source_url, meta_title, meta_description, "
    "last_built_at"
)


def _row_to_indicator(row: sqlite3.Row) -> Indicator:
    return Indicator(
        id=row["id"],
        code=row["code"],
        slug=row["slug"],
        name=row["name"],
        category=row["category"],
        frequency=row["frequency"],
        connector_type=row["connector_type"],
        connector_config=row["connector_config"],
        inception_date=date.fromisoformat(row["inception_date"]),
        expected_release_day=row["expected_release_day"],
        active=bool(row["active"]),
        last_collected_at=row["last_collected_at"],
        short_description=row["short_description"],
        long_description=row["long_description"],
        unit=row["unit"],
        source_name=row["source_name"],
        source_url=row["source_url"],
        meta_title=row["meta_title"],
        meta_description=row["meta_description"],
        last_built_at=row["last_built_at"],
    )


def list_active_indicators(conn: sqlite3.Connection) -> list[Indicator]:
    rows = fetch_all(
        conn,
        f"SELECT {_INDICATOR_COLUMNS} FROM indicators WHERE active = 1 ORDER BY code",
    )
    return [_row_to_indicator(r) for r in rows]


def get_indicator_by_code(
    conn: sqlite3.Connection, code: str
) -> Indicator | None:
    row = fetch_one(
        conn,
        f"SELECT {_INDICATOR_COLUMNS} FROM indicators WHERE code = ?",
        (code,),
    )
    return _row_to_indicator(row) if row is not None else None


def update_indicator_last_collected_at(
    conn: sqlite3.Connection, indicator_id: str, ts: str
) -> None:
    with conn:
        conn.execute(
            "UPDATE indicators SET last_collected_at = ?, updated_at = datetime('now') WHERE id = ?",
            (ts, indicator_id),
        )


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def start_collection_log(
    conn: sqlite3.Connection,
    indicator_id: str | None,
    triggered_by: str,
) -> str:
    log_id = str(uuid.uuid4())
    with conn:
        conn.execute(
            """
            INSERT INTO collection_logs (
                id, indicator_id, triggered_by, started_at, status
            ) VALUES (?, ?, ?, ?, 'running')
            """,
            (log_id, indicator_id, triggered_by, _utc_now_iso()),
        )
    return log_id


def finish_collection_log(
    conn: sqlite3.Connection,
    log_id: str,
    status: str,
    *,
    added: int = 0,
    updated: int = 0,
    error_message: str | None = None,
    raw_response: str | None = None,
) -> None:
    with conn:
        conn.execute(
            """
            UPDATE collection_logs
               SET finished_at     = ?,
                   status          = ?,
                   records_added   = ?,
                   records_updated = ?,
                   error_message   = ?,
                   raw_response    = ?
             WHERE id = ?
            """,
            (
                _utc_now_iso(),
                status,
                added,
                updated,
                error_message,
                raw_response,
                log_id,
            ),
        )


def record_skipped_collection(
    conn: sqlite3.Connection,
    indicator_id: str | None,
    triggered_by: str,
) -> str:
    log_id = start_collection_log(conn, indicator_id, triggered_by)
    finish_collection_log(conn, log_id, status="skipped")
    return log_id


@dataclass
class CollectionLog:
    id: str
    indicator_id: str | None
    indicator_code: str | None
    triggered_by: str
    started_at: str
    finished_at: str | None
    status: str
    records_added: int
    records_updated: int
    error_message: str | None


def _row_to_collection_log(row: sqlite3.Row) -> CollectionLog:
    return CollectionLog(
        id=row["id"],
        indicator_id=row["indicator_id"],
        indicator_code=row["indicator_code"],
        triggered_by=row["triggered_by"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        records_added=row["records_added"] or 0,
        records_updated=row["records_updated"] or 0,
        error_message=row["error_message"],
    )


def list_recent_collection_logs(
    conn: sqlite3.Connection, limit: int = 10
) -> list[CollectionLog]:
    rows = fetch_all(
        conn,
        """
        SELECT cl.id, cl.indicator_id, i.code AS indicator_code,
               cl.triggered_by, cl.started_at, cl.finished_at, cl.status,
               cl.records_added, cl.records_updated, cl.error_message
          FROM collection_logs cl
          LEFT JOIN indicators i ON i.id = cl.indicator_id
         ORDER BY cl.started_at DESC
         LIMIT ?
        """,
        (limit,),
    )
    return [_row_to_collection_log(r) for r in rows]


def list_recent_collection_errors(
    conn: sqlite3.Connection, since: datetime
) -> list[CollectionLog]:
    rows = fetch_all(
        conn,
        """
        SELECT cl.id, cl.indicator_id, i.code AS indicator_code,
               cl.triggered_by, cl.started_at, cl.finished_at, cl.status,
               cl.records_added, cl.records_updated, cl.error_message
          FROM collection_logs cl
          LEFT JOIN indicators i ON i.id = cl.indicator_id
         WHERE cl.status = 'error'
           AND cl.started_at >= ?
         ORDER BY cl.started_at DESC
        """,
        (since.strftime("%Y-%m-%dT%H:%M:%SZ"),),
    )
    return [_row_to_collection_log(r) for r in rows]


def update_indicator_last_built_at(
    conn: sqlite3.Connection, indicator_id: str, ts: str
) -> None:
    with conn:
        conn.execute(
            "UPDATE indicators SET last_built_at = ?, updated_at = datetime('now') WHERE id = ?",
            (ts, indicator_id),
        )


@dataclass
class BuildLog:
    id: str
    triggered_by: str
    started_at: str
    finished_at: str | None
    status: str
    indicators_updated: str | None
    files_generated: int | None
    git_commit_sha: str | None
    error_message: str | None


def start_build_log(conn: sqlite3.Connection, triggered_by: str) -> str:
    log_id = str(uuid.uuid4())
    with conn:
        conn.execute(
            """
            INSERT INTO build_logs (
                id, triggered_by, started_at, status
            ) VALUES (?, ?, ?, 'running')
            """,
            (log_id, triggered_by, _utc_now_iso()),
        )
    return log_id


def finish_build_log(
    conn: sqlite3.Connection,
    log_id: str,
    status: str,
    *,
    indicators_updated: list[str] | None = None,
    files_generated: int | None = None,
    error_message: str | None = None,
) -> None:
    payload = ",".join(indicators_updated) if indicators_updated else None
    with conn:
        conn.execute(
            """
            UPDATE build_logs
               SET finished_at        = ?,
                   status             = ?,
                   indicators_updated = ?,
                   files_generated    = ?,
                   error_message      = ?
             WHERE id = ?
            """,
            (
                _utc_now_iso(),
                status,
                payload,
                files_generated,
                error_message,
                log_id,
            ),
        )


def update_build_log_commit(
    conn: sqlite3.Connection, log_id: str, git_commit_sha: str
) -> None:
    with conn:
        conn.execute(
            "UPDATE build_logs SET git_commit_sha = ? WHERE id = ?",
            (git_commit_sha, log_id),
        )


def get_last_successful_build(conn: sqlite3.Connection) -> BuildLog | None:
    row = fetch_one(
        conn,
        """
        SELECT id, triggered_by, started_at, finished_at, status,
               indicators_updated, files_generated, git_commit_sha, error_message
          FROM build_logs
         WHERE status = 'success'
         ORDER BY started_at DESC
         LIMIT 1
        """,
    )
    if row is None:
        return None
    return BuildLog(
        id=row["id"],
        triggered_by=row["triggered_by"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        indicators_updated=row["indicators_updated"],
        files_generated=row["files_generated"],
        git_commit_sha=row["git_commit_sha"],
        error_message=row["error_message"],
    )


def apply_pending_migrations(
    conn: sqlite3.Connection,
    migrations_dir: Path,
) -> list[str]:
    """Apply *.sql migrations in `migrations_dir` not yet recorded in _migrations.

    Each pending file runs inside a transaction together with the INSERT into
    _migrations, so a failure leaves the database untouched. Returns the list
    of migration filenames applied in this call (empty when up-to-date).
    """
    conn.executescript(_MIGRATIONS_TABLE_DDL)

    applied = {row["name"] for row in fetch_all(conn, "SELECT name FROM _migrations")}
    pending = sorted(p for p in migrations_dir.glob("*.sql") if p.name not in applied)

    newly_applied: list[str] = []
    for migration in pending:
        sql = migration.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql)
            conn.execute("INSERT INTO _migrations (name) VALUES (?)", (migration.name,))
        newly_applied.append(migration.name)

    return newly_applied
