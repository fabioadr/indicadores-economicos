from __future__ import annotations

from argparse import Namespace
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.cli import cmd_gsc_collect, cmd_gsc_report, cmd_gsc_sites
from pipeline.db.connection import apply_pending_migrations, get_connection
from pipeline.gsc.collect import GscCollectResult
from pipeline.gsc.report import GscBriefing, Totals

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test.db"
    conn = get_connection(p)
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    conn.close()
    return p


def test_gsc_sites_exits_without_site_url(monkeypatch):
    monkeypatch.setattr("pipeline.cli.config.GSC_SITE_URL", None)
    with pytest.raises(SystemExit) as exc:
        cmd_gsc_sites(Namespace())
    assert exc.value.code == 2


def test_gsc_sites_exits_without_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr("pipeline.cli.config.GSC_SITE_URL", "sc-domain:example.com")
    monkeypatch.setattr(
        "pipeline.cli.config.GSC_CREDENTIALS_PATH", tmp_path / "missing.json"
    )
    with pytest.raises(SystemExit) as exc:
        cmd_gsc_sites(Namespace())
    assert exc.value.code == 2


def test_gsc_collect_success(monkeypatch, db_path, capsys):
    creds = db_path.parent / "sa.json"
    creds.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
    monkeypatch.setattr("pipeline.cli.config.GSC_SITE_URL", "sc-domain:example.com")
    monkeypatch.setattr("pipeline.cli.config.GSC_CREDENTIALS_PATH", creds)

    result = GscCollectResult(
        appearance_rows=0,
        days_empty=0,
        days_ok=1,
        end=date(2026, 9, 10),
        rows_upserted=3,
        start=date(2026, 9, 10),
    )
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = None

    with (
        patch("pipeline.gsc.client.GscClient", return_value=fake_client),
        patch("pipeline.gsc.collect.collect", return_value=result) as mock_collect,
        patch("pipeline.bot.notifications.send_gsc_collect_success") as mock_ok,
        patch("pipeline.bot.notifications.send_gsc_collect_error") as mock_err,
    ):
        rc = cmd_gsc_collect(
            Namespace(backfill=False, notify=False, since=None, until=None)
        )
    assert rc == 0
    mock_collect.assert_called_once()
    mock_ok.assert_not_called()
    mock_err.assert_not_called()
    assert "days_ok=1" in capsys.readouterr().out


def test_gsc_report_sends_telegram(monkeypatch, db_path):
    monkeypatch.setattr("pipeline.cli.config.DB_PATH", db_path)
    briefing = GscBriefing(
        current=Totals(clicks=0, ctr=0, impressions=0, position=0),
        previous=Totals(clicks=0, ctr=0, impressions=0, position=0),
        window_end=date(2026, 9, 10),
        window_start=date(2026, 9, 4),
    )
    with (
        patch("pipeline.gsc.report.build_briefing", return_value=briefing),
        patch("pipeline.bot.notifications.send_gsc_report") as mock_send,
    ):
        rc = cmd_gsc_report(Namespace(days=7))
    assert rc == 0
    mock_send.assert_called_once()
