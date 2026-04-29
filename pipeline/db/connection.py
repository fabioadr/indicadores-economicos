"""SQLite connection helpers, migration runner, and domain accessors.

M1 brought connection/migration plumbing; M3 layers on the domain helpers used
by the collector and the aggregation logic (`upsert_value`, `list_values`,
`get_last_value_date`, `batch_update_aggregations`).
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
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
