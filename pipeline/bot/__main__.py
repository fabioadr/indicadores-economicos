"""Entry point: `python -m pipeline.bot`.

Inicia long polling do Telegram com os handlers do módulo. Roda em
foreground (debug) ou via systemd --user (produção, ver
scripts/install_systemd.sh).
"""

from __future__ import annotations

import logging
import sys

from telegram.ext import Application, CommandHandler

from pipeline import config
from pipeline.bot import handlers
from pipeline.db.connection import apply_pending_migrations, get_connection

logger = logging.getLogger(__name__)


def _apply_pending_migrations() -> None:
    """Aplica migrations pendentes no startup do bot.

    Sem isto, indicadores novos (adicionados via migration SQL) ficam invisíveis
    para `/coletar all` até alguém rodar `pipeline.cli migrate` no mesmo DB.
    """
    conn = get_connection(config.DB_PATH)
    try:
        applied = apply_pending_migrations(conn, config.MIGRATIONS_DIR)
    finally:
        conn.close()
    if applied:
        logger.info("Migrations aplicadas no startup: %s", ", ".join(applied))
    else:
        logger.info("Nenhuma migration pendente no startup")


def build_application() -> Application:
    if not config.TELEGRAM_BOT_TOKEN:
        print(
            "TELEGRAM_BOT_TOKEN ausente em pipeline/.env — não é possível iniciar o bot.",
            file=sys.stderr,
        )
        sys.exit(2)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("help", handlers.cmd_help))
    app.add_handler(CommandHandler("status", handlers.cmd_status))
    app.add_handler(CommandHandler("indicadores", handlers.cmd_indicadores))
    app.add_handler(CommandHandler("coletar", handlers.cmd_coletar))
    app.add_handler(CommandHandler("migrar", handlers.cmd_migrar))
    app.add_handler(CommandHandler("publicar", handlers.cmd_publicar))
    app.add_handler(CommandHandler("logs", handlers.cmd_logs))
    app.add_handler(CommandHandler("erros", handlers.cmd_erros))
    app.add_handler(CommandHandler("cancelar", handlers.cmd_cancelar))
    app.add_handler(CommandHandler("agendamento", handlers.cmd_agendamento))
    app.add_handler(CommandHandler("agendar", handlers.cmd_agendar))
    app.add_handler(CommandHandler("pausar", handlers.cmd_pausar))
    app.add_handler(CommandHandler("retomar", handlers.cmd_retomar))
    return app


def main() -> None:
    config.setup_logging()
    _apply_pending_migrations()
    app = build_application()
    logger.info("Iniciando bot Telegram em modo long-polling")
    app.run_polling()


if __name__ == "__main__":
    main()
