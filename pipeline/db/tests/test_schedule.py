"""Testes para as funções de schedule_overrides em pipeline.db.connection."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.db.connection import (
    ScheduleOverride,
    apply_pending_migrations,
    fetch_all,
    get_active_schedule,
    get_connection,
    set_active_schedule,
    set_schedule_enabled,
    update_schedule_next_run,
    update_schedule_run,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()


class TestGetActiveSchedule:
    def test_returns_seed_row(self, db_conn):
        cfg = get_active_schedule(db_conn)
        assert cfg is not None
        assert cfg.cron_expression == "0 7 * * *"
        assert cfg.enabled is True

    def test_returns_none_on_empty_table(self, tmp_path):
        # Banco sem migrations (tabela não existe) → deve retornar None ou erro?
        # Usamos banco com migrations mas sem seed; deletamos a linha seed.
        db_path = tmp_path / "empty.db"
        conn = get_connection(db_path)
        apply_pending_migrations(conn, MIGRATIONS_DIR)
        with conn:
            conn.execute("DELETE FROM schedule_overrides")
        result = get_active_schedule(conn)
        assert result is None
        conn.close()


class TestSetActiveSchedule:
    def test_inserts_new_row_and_disables_old(self, db_conn):
        cfg = set_active_schedule(db_conn, "0 8 * * *")
        assert cfg.cron_expression == "0 8 * * *"
        assert cfg.enabled is True

        rows = fetch_all(db_conn, "SELECT cron_expression, enabled FROM schedule_overrides ORDER BY created_at")
        assert len(rows) == 2
        assert rows[0]["cron_expression"] == "0 7 * * *"
        assert rows[0]["enabled"] == 0
        assert rows[1]["cron_expression"] == "0 8 * * *"
        assert rows[1]["enabled"] == 1

    def test_returns_schedule_override(self, db_conn):
        cfg = set_active_schedule(db_conn, "0 9 * * 1-5", description="Dias úteis")
        assert isinstance(cfg, ScheduleOverride)
        assert cfg.description == "Dias úteis"

    def test_multiple_successive_updates(self, db_conn):
        set_active_schedule(db_conn, "0 8 * * *")
        set_active_schedule(db_conn, "0 9 * * *")
        active = get_active_schedule(db_conn)
        assert active is not None
        assert active.cron_expression == "0 9 * * *"
        rows = fetch_all(db_conn, "SELECT enabled FROM schedule_overrides")
        enabled_count = sum(1 for r in rows if r["enabled"])
        assert enabled_count == 1


class TestSetScheduleEnabled:
    def test_disable(self, db_conn):
        result = set_schedule_enabled(db_conn, False)
        assert result is not None
        assert result.enabled is False
        cfg = get_active_schedule(db_conn)
        assert cfg is not None
        assert cfg.enabled is False

    def test_reenable(self, db_conn):
        set_schedule_enabled(db_conn, False)
        result = set_schedule_enabled(db_conn, True)
        assert result is not None
        assert result.enabled is True

    def test_returns_none_on_empty_table(self, tmp_path):
        db_path = tmp_path / "empty2.db"
        conn = get_connection(db_path)
        apply_pending_migrations(conn, MIGRATIONS_DIR)
        with conn:
            conn.execute("DELETE FROM schedule_overrides")
        result = set_schedule_enabled(conn, True)
        assert result is None
        conn.close()


class TestUpdateScheduleRun:
    def test_updates_last_run_at(self, db_conn):
        cfg = get_active_schedule(db_conn)
        assert cfg is not None
        update_schedule_run(db_conn, cfg.id, "2026-05-06T07:00:00")
        updated = get_active_schedule(db_conn)
        assert updated is not None
        assert updated.last_run_at == "2026-05-06T07:00:00"


class TestUpdateScheduleNextRun:
    def test_updates_next_run_at(self, db_conn):
        cfg = get_active_schedule(db_conn)
        assert cfg is not None
        update_schedule_next_run(db_conn, cfg.id, "2026-05-07T07:00:00")
        updated = get_active_schedule(db_conn)
        assert updated is not None
        assert updated.next_run_at == "2026-05-07T07:00:00"
