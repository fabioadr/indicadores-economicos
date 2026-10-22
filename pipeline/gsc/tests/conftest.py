from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.db.connection import apply_pending_migrations, get_connection

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()
