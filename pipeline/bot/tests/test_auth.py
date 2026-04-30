"""Tests for pipeline/bot/auth: chat-id whitelist decorator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pipeline.bot import auth


def _fake_update():
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


def test_authorized_chat_passes(monkeypatch):
    monkeypatch.setattr(auth.config, "TELEGRAM_CHAT_ID", "42")
    update = _fake_update()
    update.effective_chat.id = 42

    inner = AsyncMock()

    @auth.authorized_only
    async def handler(update, context):
        await inner(update, context)

    asyncio.run(handler(update, MagicMock()))
    inner.assert_awaited_once()
    update.message.reply_text.assert_not_called()


def test_unauthorized_chat_replies_and_skips(monkeypatch):
    monkeypatch.setattr(auth.config, "TELEGRAM_CHAT_ID", "42")
    update = _fake_update()
    update.effective_chat.id = 99

    inner = AsyncMock()

    @auth.authorized_only
    async def handler(update, context):
        await inner(update, context)

    asyncio.run(handler(update, MagicMock()))
    inner.assert_not_awaited()
    update.message.reply_text.assert_awaited_once_with("⛔ Não autorizado.")


def test_missing_chat_id_blocks(monkeypatch):
    monkeypatch.setattr(auth.config, "TELEGRAM_CHAT_ID", None)
    update = _fake_update()
    update.effective_chat.id = 42

    inner = AsyncMock()

    @auth.authorized_only
    async def handler(update, context):
        await inner(update, context)

    asyncio.run(handler(update, MagicMock()))
    inner.assert_not_awaited()
    update.message.reply_text.assert_awaited_once_with("⛔ Não autorizado.")
