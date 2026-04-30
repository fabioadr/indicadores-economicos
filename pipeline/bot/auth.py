"""Decorator de autorização — whitelist single-user via TELEGRAM_CHAT_ID."""

from __future__ import annotations

import functools
import logging
from typing import Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes

from pipeline import config
from pipeline.bot import formatters

logger = logging.getLogger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def authorized_only(func: Handler) -> Handler:
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id_raw = config.TELEGRAM_CHAT_ID
        if chat_id_raw is None:
            logger.warning(
                "TELEGRAM_CHAT_ID não configurado; bloqueando comando %s",
                func.__name__,
            )
            if update.message:
                await update.message.reply_text(formatters.unauthorized_message())
            return
        try:
            allowed_id = int(chat_id_raw)
        except ValueError:
            logger.error("TELEGRAM_CHAT_ID inválido: %r", chat_id_raw)
            return
        if update.effective_chat is None or update.effective_chat.id != allowed_id:
            logger.warning(
                "Comando rejeitado de chat %s (allowed=%s)",
                update.effective_chat.id if update.effective_chat else None,
                allowed_id,
            )
            if update.message:
                await update.message.reply_text(formatters.unauthorized_message())
            return
        return await func(update, context)

    return wrapper
