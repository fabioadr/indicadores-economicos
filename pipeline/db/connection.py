"""SQLite connection helpers and migration runner.

Minimal surface area for Milestone 1: open connections, run scripts, and apply
pending migrations from `pipeline/db/migrations/`. Domain helpers (upsert_value,
list_values, etc.) come in M3.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

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
