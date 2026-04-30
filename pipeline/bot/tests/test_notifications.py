"""Tests for pipeline/bot/notifications: httpx-based fail-quiet sends."""

from __future__ import annotations

import httpx
import pytest
import respx

from pipeline.bot import notifications


@pytest.fixture(autouse=True)
def _reset_warning_flag(monkeypatch):
    monkeypatch.setattr(notifications, "_warned_missing_credentials", False)


def test_send_message_noop_when_no_token(monkeypatch, caplog):
    monkeypatch.setattr(notifications.config, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(notifications.config, "TELEGRAM_CHAT_ID", "123")

    with caplog.at_level("WARNING"):
        notifications.send_message("hello")

    assert any("Telegram não configurado" in r.message for r in caplog.records)


def test_send_message_noop_when_no_chat_id(monkeypatch):
    monkeypatch.setattr(notifications.config, "TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setattr(notifications.config, "TELEGRAM_CHAT_ID", None)

    # Should not raise and should not call any HTTP endpoint
    notifications.send_message("hello")


@respx.mock
def test_send_message_posts_to_bot_api(monkeypatch):
    monkeypatch.setattr(notifications.config, "TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setattr(notifications.config, "TELEGRAM_CHAT_ID", "42")

    route = respx.post("https://api.telegram.org/botabc/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    notifications.send_message("oi")

    assert route.called
    payload = route.calls.last.request.read()
    assert b'"chat_id":"42"' in payload
    assert b'"text":"oi"' in payload


@respx.mock
def test_send_message_swallows_http_errors(monkeypatch, caplog):
    monkeypatch.setattr(notifications.config, "TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setattr(notifications.config, "TELEGRAM_CHAT_ID", "42")

    respx.post("https://api.telegram.org/botabc/sendMessage").mock(
        return_value=httpx.Response(500, text="boom")
    )

    with caplog.at_level("WARNING"):
        notifications.send_message("oi")  # must not raise

    assert any("falhou" in r.message for r in caplog.records)


@respx.mock
def test_send_message_swallows_network_errors(monkeypatch, caplog):
    monkeypatch.setattr(notifications.config, "TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setattr(notifications.config, "TELEGRAM_CHAT_ID", "42")

    respx.post("https://api.telegram.org/botabc/sendMessage").mock(
        side_effect=httpx.ConnectError("no network")
    )

    with caplog.at_level("WARNING"):
        notifications.send_message("oi")  # must not raise

    assert any("erro" in r.message for r in caplog.records)
