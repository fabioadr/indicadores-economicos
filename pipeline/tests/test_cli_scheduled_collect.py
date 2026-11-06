"""Testes para `pipeline.cli scheduled-collect`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.cli import cmd_scheduled_collect
from pipeline.core.scheduler import CollectResult
from pipeline.db.connection import (
    apply_pending_migrations,
    get_active_schedule,
    get_connection,
    set_schedule_enabled,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test.db"
    conn = get_connection(p)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    conn.close()
    return p


def _set_last_run(db_path, value):
    conn = get_connection(db_path)
    with conn:
        conn.execute("UPDATE schedule_overrides SET last_run_at = ?", (value,))
    conn.close()


def _fake_clock(mock_dt, now):
    mock_dt.now.return_value = now
    mock_dt.fromisoformat = datetime.fromisoformat


def _args():
    return MagicMock()


def _result(added=0, updated=0, code="IPCA", error=None):
    return CollectResult(code=code, added=added, updated=updated, error=error)


class TestScheduledCollectSkips:
    def test_skips_when_schedule_paused(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        set_schedule_enabled(conn, False)
        conn.close()

        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        with patch("pipeline.cli.scheduler.run_all") as mock_run:
            rc = cmd_scheduled_collect(_args())
        assert rc == 0
        mock_run.assert_not_called()

    def test_skips_when_latest_slot_already_ran(self, db_path, monkeypatch):
        # Seed é 0 7 * * *; a execução das 07h de hoje já rodou → 14:30 não coleta.
        _set_last_run(db_path, "2026-05-06T07:00:41")
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 14, 30)
        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all") as mock_run:
            _fake_clock(mock_dt, fake_now)
            rc = cmd_scheduled_collect(_args())
        assert rc == 0
        mock_run.assert_not_called()

    def test_skips_before_todays_slot_when_yesterday_ran(self, db_path, monkeypatch):
        _set_last_run(db_path, "2026-05-05T07:00:10")
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 6, 0)
        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all") as mock_run:
            _fake_clock(mock_dt, fake_now)
            rc = cmd_scheduled_collect(_args())
        assert rc == 0
        mock_run.assert_not_called()

    def test_skips_when_no_schedule(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM schedule_overrides")
        conn.close()

        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        with patch("pipeline.cli.scheduler.run_all") as mock_run:
            rc = cmd_scheduled_collect(_args())
        assert rc == 0
        mock_run.assert_not_called()


class TestScheduledCollectExecutes:
    def test_catches_up_missed_slot(self, db_path, monkeypatch):
        # Host desligado às 07h; primeira execução do cron às 08h deve coletar.
        _set_last_run(db_path, "2026-05-05T07:00:10")
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 8, 0)
        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[]) as mock_run:
            _fake_clock(mock_dt, fake_now)
            rc = cmd_scheduled_collect(_args())
        assert rc == 0
        mock_run.assert_called_once()

    def test_catches_up_after_several_missed_days_only_once(self, db_path, monkeypatch):
        _set_last_run(db_path, "2026-05-01T07:00:00")
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[]) as mock_run:
            _fake_clock(mock_dt, datetime(2026, 5, 6, 9, 0))
            cmd_scheduled_collect(_args())
            _fake_clock(mock_dt, datetime(2026, 5, 6, 10, 0))
            cmd_scheduled_collect(_args())
        assert mock_run.call_count == 1

    def test_runs_collect_when_cron_matches(self, db_path, monkeypatch):
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 7, 0)  # bate com 0 7 * * *

        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[]) as mock_run, \
             patch("pipeline.cli.builder.build") as mock_build, \
             patch("pipeline.cli.builder.deploy") as mock_deploy:
            mock_dt.now.return_value = fake_now
            rc = cmd_scheduled_collect(_args())

        assert rc == 0
        mock_run.assert_called_once()
        # Sem mudanças → build não chamado
        mock_build.assert_not_called()
        mock_deploy.assert_not_called()

    def test_runs_build_when_changes(self, db_path, monkeypatch):
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 7, 0)
        build_result = MagicMock()
        build_result.status = "success"

        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[_result(added=1)]), \
             patch("pipeline.cli.builder.build", return_value=build_result) as mock_build, \
             patch("pipeline.cli.builder.deploy") as mock_deploy:
            mock_dt.now.return_value = fake_now
            rc = cmd_scheduled_collect(_args())

        assert rc == 0
        mock_build.assert_called_once()
        mock_deploy.assert_called_once()

    def test_no_deploy_when_no_changes(self, db_path, monkeypatch):
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 7, 0)

        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[_result(added=0, updated=0)]), \
             patch("pipeline.cli.builder.build") as mock_build, \
             patch("pipeline.cli.builder.deploy") as mock_deploy:
            mock_dt.now.return_value = fake_now
            rc = cmd_scheduled_collect(_args())

        assert rc == 0
        mock_build.assert_not_called()
        mock_deploy.assert_not_called()

    def test_returns_1_when_build_fails(self, db_path, monkeypatch):
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 7, 0)

        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[_result(added=1)]), \
             patch("pipeline.cli.builder.build", side_effect=RuntimeError("boom")), \
             patch("pipeline.cli.builder.deploy") as mock_deploy:
            mock_dt.now.return_value = fake_now
            rc = cmd_scheduled_collect(_args())

        assert rc == 1
        mock_deploy.assert_not_called()

    def test_updates_last_run_at(self, db_path, monkeypatch):
        monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
        fake_now = datetime(2026, 5, 6, 7, 0)

        with patch("pipeline.cli.datetime") as mock_dt, \
             patch("pipeline.cli.scheduler.run_all", return_value=[]), \
             patch("pipeline.cli.builder.build"), \
             patch("pipeline.cli.builder.deploy"):
            mock_dt.now.return_value = fake_now
            cmd_scheduled_collect(_args())

        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.last_run_at == fake_now.isoformat()
