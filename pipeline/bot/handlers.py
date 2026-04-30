"""Async handlers para os comandos do bot.

Operações síncronas (scheduler/builder) rodam em `asyncio.to_thread` para
não bloquear o loop de eventos do python-telegram-bot.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from pipeline import config
from pipeline.bot import formatters
from pipeline.bot.auth import authorized_only
from pipeline.core import builder, scheduler
from pipeline.db.connection import (
    get_connection,
    get_indicator_by_code,
    get_last_successful_build,
    list_active_indicators,
    list_recent_collection_errors,
    list_recent_collection_logs,
    list_values,
)

logger = logging.getLogger(__name__)


async def _reply(update: Update, text: str) -> None:
    if update.message is None:
        return
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@authorized_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, formatters.help_message())


@authorized_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, formatters.help_message())


@authorized_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            indicators = list_active_indicators(conn)
            last_build = get_last_successful_build(conn)
            since = datetime.now(tz=timezone.utc) - timedelta(hours=24)
            errors = list_recent_collection_errors(conn, since)
            return formatters.status_message(
                active_count=len(indicators),
                last_build=last_build,
                errors_24h=len(errors),
            )
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_indicadores(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            indicators = list_active_indicators(conn)
            latest_by_id = {}
            for ind in indicators:
                vals = list_values(conn, ind.id, order="desc")
                latest_by_id[ind.id] = vals[0] if vals else None
            return formatters.indicators_message(indicators, latest_by_id)
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_coletar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args: list[str] = list(context.args) if context.args else []
    if not args:
        def list_codes() -> str:
            conn = get_connection(config.DB_PATH)
            try:
                indicators = list_active_indicators(conn)
                codes = " | ".join(ind.code for ind in indicators)
                return (
                    f"Uso: /coletar &lt;CODE|all&gt;\n\n"
                    f"Indicadores disponíveis: {codes}\n"
                    f"Ou use /coletar all para coletar todos."
                )
            finally:
                conn.close()

        await _reply(update, await asyncio.to_thread(list_codes))
        return
    target = args[0].strip()

    if target.lower() == "all":
        await _reply(update, "🔄 Rodando coleta em todos os indicadores...")

        def work_all() -> list[scheduler.CollectResult]:
            conn = get_connection(config.DB_PATH)
            try:
                return scheduler.run_all(conn, triggered_by="telegram")
            finally:
                conn.close()

        results = await asyncio.to_thread(work_all)
        await _reply(update, formatters.collect_summary_message(results))
        return

    # Coleta de um indicador específico
    await _reply(update, formatters.collect_starting_message(target))

    def work_single() -> tuple[scheduler.CollectResult | None, object]:
        conn = get_connection(config.DB_PATH)
        try:
            indicator = get_indicator_by_code(conn, target.upper())
            if indicator is None:
                return None, None
            result = scheduler.collect_single(
                conn, indicator, triggered_by="telegram"
            )
            vals = list_values(conn, indicator.id, order="desc")
            latest = vals[0] if vals else None
            return result, latest
        finally:
            conn.close()

    result, latest = await asyncio.to_thread(work_single)
    if result is None:
        await _reply(update, f"❓ Indicador desconhecido: {target}")
        return
    await _reply(update, formatters.collect_result_message(result, latest))


@authorized_only
async def cmd_publicar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "🛠 Rodando build...")

    def work() -> builder.BuildResult:
        conn = get_connection(config.DB_PATH)
        try:
            return builder.build(conn, triggered_by="telegram")
        finally:
            conn.close()

    try:
        result = await asyncio.to_thread(work)
    except Exception as exc:  # noqa: BLE001
        logger.exception("publicar falhou")
        await _reply(update, formatters.build_error_message(exc))
        return

    if result.status == "no_changes":
        await _reply(update, "ℹ️ Nenhum indicador precisava de rebuild.")
        return
    await _reply(update, formatters.build_success_message(result))


@authorized_only
async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args: list[str] = list(context.args) if context.args else []
    limit = 10
    if args:
        try:
            limit = max(1, min(50, int(args[0])))
        except ValueError:
            await _reply(update, "Uso: /logs [n]  (n inteiro)")
            return
    # fallback: parse from message text when context.args is unexpectedly empty
    elif update.message and update.message.text:
        parts = update.message.text.strip().split()
        if len(parts) >= 2:
            try:
                limit = max(1, min(50, int(parts[1])))
            except ValueError:
                pass
    logger.debug("cmd_logs: args=%r limit=%d", args, limit)

    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            logs = list_recent_collection_logs(conn, limit=limit)
            return formatters.logs_message(logs)
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_erros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            since = datetime.now(tz=timezone.utc) - timedelta(hours=24)
            errors = list_recent_collection_errors(conn, since)
            return formatters.errors_message(errors)
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "ℹ️ Operações são síncronas e curtas — nada para cancelar no momento.",
    )
