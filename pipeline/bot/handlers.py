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
from pipeline.core.cron import next_run as _cron_next_run, validate_frequency
from pipeline.db.connection import (
    get_active_schedule,
    get_connection,
    get_indicator_by_code,
    get_last_successful_build,
    list_active_indicators,
    list_recent_collection_errors,
    list_recent_collection_logs,
    list_values,
    set_active_schedule,
    set_schedule_enabled,
    update_schedule_next_run,
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
            schedule = get_active_schedule(conn)
            return formatters.status_message(
                active_count=len(indicators),
                last_build=last_build,
                errors_24h=len(errors),
                schedule=schedule,
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
    await _reply(update, "🛠 Rodando build + deploy...")

    def work() -> tuple[builder.BuildResult, builder.DeployResult | None, BaseException | None]:
        conn = get_connection(config.DB_PATH)
        try:
            build_result = builder.build(conn, triggered_by="telegram")
            if build_result.status != "success":
                return build_result, None, None
            try:
                deploy_result = builder.deploy(
                    conn, build_result, triggered_by="telegram"
                )
            except Exception as exc:  # noqa: BLE001
                return build_result, None, exc
            return build_result, deploy_result, None
        finally:
            conn.close()

    try:
        build_result, deploy_result, deploy_exc = await asyncio.to_thread(work)
    except Exception as exc:  # noqa: BLE001
        logger.exception("publicar falhou")
        await _reply(update, formatters.build_error_message(exc))
        return

    if build_result.status == "no_changes":
        await _reply(update, "ℹ️ Nenhum indicador precisava de rebuild.")
        return

    if deploy_exc is not None:
        await _reply(update, formatters.build_success_message(build_result))
        await _reply(update, formatters.deploy_error_message(deploy_exc))
        return

    await _reply(update, formatters.publish_summary_message(build_result, deploy_result))


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


@authorized_only
async def cmd_agendamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            cfg = get_active_schedule(conn)
            if cfg is None:
                return "⚠️ Nenhum agendamento configurado. Use /agendar para criar."
            return formatters.format_schedule(cfg)
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_agendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args: list[str] = list(context.args) if context.args else []
    if not args:
        await _reply(
            update,
            "Uso: /agendar &lt;expressão cron&gt;\n"
            "Exemplo: /agendar 0 8 * * *\n\n"
            "Exemplos válidos:\n"
            "  0 7 * * *     (todo dia às 07:00)\n"
            "  0 8,18 * * *  (08:00 e 18:00)\n"
            "  0 9 * * 1-5   (seg a sex às 09:00)",
        )
        return

    expression = " ".join(args)

    try:
        from croniter import croniter
        croniter(expression, datetime.now())
    except (ValueError, KeyError) as exc:
        await _reply(
            update,
            f"❌ Expressão cron inválida\n\nErro: {exc}\n\n"
            "Exemplos válidos:\n"
            "  0 7 * * *     (todo dia às 07:00)\n"
            "  0 8,18 * * *  (08:00 e 18:00)\n"
            "  0 9 * * 1-5   (seg a sex às 09:00)",
        )
        return

    if not validate_frequency(expression):
        await _reply(
            update,
            "❌ Frequência muito alta. O campo de minutos deve ser um valor literal único.\n\n"
            "Exemplos rejeitados: */15, *, 0,30\n"
            "Exemplos aceitos: 0, 7, 30",
        )
        return

    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            cfg = set_active_schedule(conn, expression)
            try:
                nr = _cron_next_run(expression, datetime.now())
                update_schedule_next_run(conn, cfg.id, nr.isoformat())
                next_str = nr.strftime("%d/%m %H:%M")
            except Exception:  # noqa: BLE001
                next_str = "—"
            return (
                f"✅ Novo agendamento configurado\n\n"
                f"Expressão: <code>{expression}</code>\n"
                f"Próxima execução: {next_str}"
            )
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)


@authorized_only
async def cmd_pausar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def work() -> None:
        conn = get_connection(config.DB_PATH)
        try:
            set_schedule_enabled(conn, False)
        finally:
            conn.close()

    await asyncio.to_thread(work)
    await _reply(
        update,
        "⏸ Agendamento pausado.\n\n"
        "A coleta automática está desativada. Use /retomar para reativar.\n"
        "Você ainda pode coletar manualmente com /coletar all.",
    )


@authorized_only
async def cmd_retomar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def work() -> str:
        conn = get_connection(config.DB_PATH)
        try:
            cfg = get_active_schedule(conn)
            if cfg is None:
                return "⚠️ Nenhum agendamento configurado. Use /agendar primeiro."
            updated = set_schedule_enabled(conn, True)
            if updated is None:
                return "⚠️ Nenhum agendamento configurado. Use /agendar primeiro."
            try:
                nr = _cron_next_run(updated.cron_expression, datetime.now())
                update_schedule_next_run(conn, updated.id, nr.isoformat())
                next_str = nr.strftime("%d/%m %H:%M")
            except Exception:  # noqa: BLE001
                next_str = "—"
            return (
                f"▶️ Agendamento retomado\n\n"
                f"Expressão atual: <code>{updated.cron_expression}</code>\n"
                f"Próxima execução: {next_str}"
            )
        finally:
            conn.close()

    text = await asyncio.to_thread(work)
    await _reply(update, text)
