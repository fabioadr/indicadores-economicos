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
    updates: list[
        tuple[str, float | None, float | None, float | None, float | None]
    ],
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
    aggregation_mode: str = "compound_monthly"


_INDICATOR_COLUMNS = (
    "id, code, slug, name, category, frequency, "
    "connector_type, connector_config, inception_date, "
    "expected_release_day, active, last_collected_at, "
    "short_description, long_description, unit, "
    "source_name, source_url, meta_title, meta_description, "
    "last_built_at, aggregation_mode"
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
        aggregation_mode=row["aggregation_mode"],
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


@dataclass(frozen=True)
class ScheduleOverride:
    id: str
    cron_expression: str
    enabled: bool
    last_run_at: str | None
    next_run_at: str | None
    description: str | None
    created_at: str
    updated_at: str


def _row_to_schedule(row: sqlite3.Row) -> ScheduleOverride:
    return ScheduleOverride(
        id=row["id"],
        cron_expression=row["cron_expression"],
        enabled=bool(row["enabled"]),
        last_run_at=row["last_run_at"],
        next_run_at=row["next_run_at"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_active_schedule(conn: sqlite3.Connection) -> ScheduleOverride | None:
    """Linha ativa atual: enabled=1 mais recente; cai pra enabled=0 mais recente
    se não houver ativa (preserva o histórico de configs anteriores)."""
    row = fetch_one(
        conn,
        """
        SELECT id, cron_expression, enabled, last_run_at, next_run_at,
               description, created_at, updated_at
          FROM schedule_overrides
         ORDER BY enabled DESC, updated_at DESC
         LIMIT 1
        """,
    )
    return _row_to_schedule(row) if row else None


def set_active_schedule(
    conn: sqlite3.Connection,
    cron_expression: str,
    description: str | None = None,
) -> ScheduleOverride:
    """Desativa as linhas atuais (enabled=1 → 0) e insere uma nova com enabled=1.

    Mantém histórico das configurações anteriores (decisão do doc 06).
    """
    new_id = str(uuid.uuid4())
    with conn:
        conn.execute(
            """
            UPDATE schedule_overrides
               SET enabled = 0, updated_at = datetime('now')
             WHERE enabled = 1
            """
        )
        conn.execute(
            """
            INSERT INTO schedule_overrides (id, cron_expression, enabled, description)
            VALUES (?, ?, 1, ?)
            """,
            (new_id, cron_expression, description),
        )
    row = fetch_one(
        conn,
        """
        SELECT id, cron_expression, enabled, last_run_at, next_run_at,
               description, created_at, updated_at
          FROM schedule_overrides
         WHERE id = ?
        """,
        (new_id,),
    )
    if row is None:
        raise RuntimeError("set_active_schedule: linha recém-inserida não foi encontrada")
    return _row_to_schedule(row)


def set_schedule_enabled(
    conn: sqlite3.Connection,
    enabled: bool,
) -> ScheduleOverride | None:
    """Liga/desliga a linha mais recente. Retorna a linha atualizada, ou None
    se a tabela está vazia."""
    current = get_active_schedule(conn)
    if current is None:
        return None
    with conn:
        conn.execute(
            """
            UPDATE schedule_overrides
               SET enabled = ?, updated_at = datetime('now')
             WHERE id = ?
            """,
            (1 if enabled else 0, current.id),
        )
    row = fetch_one(
        conn,
        """
        SELECT id, cron_expression, enabled, last_run_at, next_run_at,
               description, created_at, updated_at
          FROM schedule_overrides
         WHERE id = ?
        """,
        (current.id,),
    )
    return _row_to_schedule(row) if row else None


def update_schedule_run(
    conn: sqlite3.Connection,
    schedule_id: str,
    last_run_at: str,
) -> None:
    with conn:
        conn.execute(
            """
            UPDATE schedule_overrides
               SET last_run_at = ?, updated_at = datetime('now')
             WHERE id = ?
            """,
            (last_run_at, schedule_id),
        )


def update_schedule_next_run(
    conn: sqlite3.Connection,
    schedule_id: str,
    next_run_at: str,
) -> None:
    with conn:
        conn.execute(
            """
            UPDATE schedule_overrides
               SET next_run_at = ?, updated_at = datetime('now')
             WHERE id = ?
            """,
            (next_run_at, schedule_id),
        )


def upsert_release_date(
    conn: sqlite3.Connection,
    indicator_id: str,
    *,
    release_date: str,
    source: str,
    reference_period: str | None = None,
    title: str | None = None,
) -> None:
    """Insere/atualiza uma data oficial de divulgação para o indicador.

    `release_date` em ISO (YYYY-MM-DD). Idempotente via UNIQUE(indicator_id,
    release_date).
    """
    with conn:
        conn.execute(
            """
            INSERT INTO release_dates (
                id, indicator_id, release_date, reference_period, source, title
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (indicator_id, release_date) DO UPDATE SET
                reference_period = excluded.reference_period,
                source           = excluded.source,
                title            = excluded.title,
                fetched_at       = datetime('now')
            """,
            (
                str(uuid.uuid4()),
                indicator_id,
                release_date,
                reference_period,
                source,
                title,
            ),
        )


def get_next_official_release_dates(
    conn: sqlite3.Connection, today: date
) -> dict[str, date]:
    """Mapeia indicator_id -> menor `release_date` futura (>= hoje) conhecida.

    Usado pelo builder para preferir datas oficiais sobre a estimativa.
    """
    rows = fetch_all(
        conn,
        """
        SELECT indicator_id, MIN(release_date) AS d
          FROM release_dates
         WHERE release_date >= ?
         GROUP BY indicator_id
        """,
        (today.isoformat(),),
    )
    out: dict[str, date] = {}
    for row in rows:
        if row["d"] is not None:
            out[row["indicator_id"]] = date.fromisoformat(row["d"])
    return out


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
