"""Pipeline configuration: paths, env loading, and logging setup.

Single import point for any module that needs to know where the database lives,
where to write site artifacts, or where to drop the daily log file.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_ROOT = REPO_ROOT / "pipeline"
MIGRATIONS_DIR = PIPELINE_ROOT / "db" / "migrations"
LOGS_DIR = PIPELINE_ROOT / "logs"

load_dotenv(PIPELINE_ROOT / ".env")


def _path_from_env(var: str, default: Path) -> Path:
    raw = os.getenv(var)
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


DB_PATH = _path_from_env("DB_PATH", REPO_ROOT / "data" / "indicadores.db")
SITE_DATA_DIR = _path_from_env("SITE_DATA_DIR", REPO_ROOT / "site" / "data")
SITE_CHARTS_DIR = _path_from_env(
    "SITE_CHARTS_DIR", REPO_ROOT / "site" / "public" / "charts"
)
GITHUB_REPO_PATH = _path_from_env("GITHUB_REPO_PATH", REPO_ROOT)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or None
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or None

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_logging_configured = False


def setup_logging(level: str | None = None) -> None:
    """Configure root logger with stdout + daily file handler.

    Idempotent: subsequent calls are no-ops so that CLI/bot/tests can call it
    without piling up handlers.
    """
    global _logging_configured
    if _logging_configured:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{date.today().isoformat()}.log"

    resolved_level = (level or LOG_LEVEL).upper()
    root = logging.getLogger()
    root.setLevel(resolved_level)

    formatter = logging.Formatter(_LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _logging_configured = True
