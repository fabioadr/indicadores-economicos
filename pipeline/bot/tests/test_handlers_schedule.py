"""Testes para os handlers de agendamento: /agendamento, /agendar, /pausar, /retomar."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.bot import auth, handlers
from pipeline.db.connection import (
    apply_pending_migrations,
    get_active_schedule,
    get_connection,
    set_schedule_enabled,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test.db"
    conn = get_connection(p)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    conn.close()
    return p


def _update(chat_id: int = 42):
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = chat_id
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


def _context(args=None):
    ctx = MagicMock()
    ctx.args = args or []
    return ctx


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _auth_ok(monkeypatch):
    monkeypatch.setattr(auth.config, "TELEGRAM_CHAT_ID", "42")


class TestCmdAgendamento:
    def test_shows_current_schedule(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendamento(update, _context()))
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "0 7 * * *" in text
        assert "Ativo" in text

    def test_shows_paused_status(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        set_schedule_enabled(conn, False)
        conn.close()

        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendamento(update, _context()))
        text = update.message.reply_text.call_args[0][0]
        assert "Pausado" in text

    def test_shows_warning_when_no_schedule(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM schedule_overrides")
        conn.close()

        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendamento(update, _context()))
        text = update.message.reply_text.call_args[0][0]
        assert "Nenhum" in text


class TestCmdAgendar:
    def test_valid_expression_updates_db(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendar(update, _context(args=["0", "8", "*", "*", "*"])))

        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.cron_expression == "0 8 * * *"

        text = update.message.reply_text.call_args[0][0]
        assert "✅" in text
        assert "0 8 * * *" in text

    def test_invalid_expression_returns_error(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendar(update, _context(args=["foo", "bar"])))

        # DB não deve ter mudado
        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.cron_expression == "0 7 * * *"

        text = update.message.reply_text.call_args[0][0]
        assert "❌" in text

    def test_high_frequency_rejected(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendar(update, _context(args=["*/15", "*", "*", "*", "*"])))

        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.cron_expression == "0 7 * * *"

        text = update.message.reply_text.call_args[0][0]
        assert "❌" in text
        assert "Frequência" in text

    def test_no_args_shows_usage(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendar(update, _context(args=[])))
        text = update.message.reply_text.call_args[0][0]
        assert "Uso:" in text

    def test_star_in_minutes_rejected(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_agendar(update, _context(args=["*", "*", "*", "*", "*"])))
        text = update.message.reply_text.call_args[0][0]
        assert "❌" in text


class TestCmdPausar:
    def test_disables_schedule(self, db_path, monkeypatch):
        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_pausar(update, _context()))

        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.enabled is False

        text = update.message.reply_text.call_args[0][0]
        assert "pausado" in text.lower()


class TestCmdRetomar:
    def test_reenables_schedule(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        set_schedule_enabled(conn, False)
        conn.close()

        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_retomar(update, _context()))

        conn = get_connection(db_path)
        cfg = get_active_schedule(conn)
        conn.close()
        assert cfg is not None
        assert cfg.enabled is True

        text = update.message.reply_text.call_args[0][0]
        assert "retomado" in text.lower()

    def test_shows_warning_when_no_schedule(self, db_path, monkeypatch):
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM schedule_overrides")
        conn.close()

        monkeypatch.setattr(handlers.config, "DB_PATH", db_path)
        update = _update()
        _run(handlers.cmd_retomar(update, _context()))
        text = update.message.reply_text.call_args[0][0]
        assert "Nenhum" in text
