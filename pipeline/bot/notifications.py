"""Push notifications enviadas pelo pipeline para o Telegram via Bot API.

Decisão registrada em docs/07-telegram-bot.md:132 — sem queue, chamada
direta via httpx. Falha de Telegram nunca derruba o pipeline: tudo é
envelopado em try/except e logado.

Quando TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID estão ausentes, todas as
funções viram no-op (avisa uma vez via logger.warning e segue).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from pipeline import config

if TYPE_CHECKING:
    from pipeline.core.builder import BuildResult, DeployResult
    from pipeline.core.scheduler import CollectResult
    from pipeline.db.connection import Indicator

logger = logging.getLogger(__name__)

_BOT_API_BASE = "https://api.telegram.org"
_warned_missing_credentials = False


def _credentials() -> tuple[str, str] | None:
    global _warned_missing_credentials
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        if not _warned_missing_credentials:
            logger.warning(
                "Telegram não configurado (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ausentes); "
                "notificações serão ignoradas."
            )
            _warned_missing_credentials = True
        return None
    return token, chat_id


def send_message(text: str) -> None:
    creds = _credentials()
    if creds is None:
        return
    token, chat_id = creds
    try:
        response = httpx.post(
            f"{_BOT_API_BASE}/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        if response.status_code >= 400:
            logger.warning(
                "Telegram sendMessage falhou (status=%s body=%s)",
                response.status_code,
                response.text[:200],
            )
    except Exception as exc:  # noqa: BLE001 — fail-quiet para o pipeline
        logger.warning("Telegram sendMessage erro: %s", exc)


def send_collect_success(results: list["CollectResult"]) -> None:
    """Resumo de uma rodada de coleta. Chamado pelo scheduler.run_all."""
    if not results:
        return
    from pipeline.bot import formatters

    text = formatters.collect_summary_message(results)
    send_message(text)


def send_collect_error(indicator: "Indicator", error: str) -> None:
    from pipeline.bot import formatters

    send_message(formatters.collect_error_message(indicator, error))


def send_build_success(result: "BuildResult") -> None:
    from pipeline.bot import formatters

    if not result.changed:
        return
    send_message(formatters.build_success_message(result))


def send_build_error(exc: BaseException) -> None:
    from pipeline.bot import formatters

    send_message(formatters.build_error_message(exc))


def send_deploy_success(
    deploy_result: "DeployResult", build_result: "BuildResult"
) -> None:
    if deploy_result.status != "success":
        return
    from pipeline.bot import formatters

    send_message(formatters.deploy_success_message(deploy_result, build_result))


def send_deploy_error(exc: BaseException) -> None:
    from pipeline.bot import formatters

    send_message(formatters.deploy_error_message(exc))
