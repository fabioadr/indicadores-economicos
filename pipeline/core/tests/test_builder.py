"""Tests for the M5 builder: JSON shape, needs_rebuild logic, no_changes path."""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

from pipeline.connectors.base import RawDataPoint
from pipeline.core import builder
from pipeline.core.aggregations import recompute_aggregations
from pipeline.db.connection import (
    apply_pending_migrations,
    finish_build_log,
    get_connection,
    get_indicator_by_code,
    get_last_successful_build,
    list_active_indicators,
    start_build_log,
    update_indicator_last_collected_at,
    update_indicator_last_built_at,
    upsert_value,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"


@pytest.fixture
def db_conn(tmp_path):
    conn = get_connection(tmp_path / "indicadores.db")
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()


@pytest.fixture
def site_dirs(tmp_path):
    data_dir = tmp_path / "site" / "data"
    charts_dir = tmp_path / "site" / "public" / "charts"
    return data_dir, charts_dir


def _seed_ipca(conn) -> str:
    """Seed 14 monthly values so YTD and last_12m are populated."""
    ipca = get_indicator_by_code(conn, "IPCA")
    for i in range(14):
        # Distribute across two years so YTD has multiple rows.
        year = 2025 if i < 12 else 2026
        month = (i % 12) + 1
        ref = date(year, month, 1)
        upsert_value(
            conn,
            ipca.id,
            RawDataPoint(reference_date=ref, value=0.40 + 0.01 * i, raw_value="x"),
        )
    recompute_aggregations(conn, ipca.id)
    update_indicator_last_collected_at(conn, ipca.id, "2026-04-29T10:00:00Z")
    return ipca.id


def test_needs_rebuild_logic(db_conn):
    ipca = get_indicator_by_code(db_conn, "IPCA")
    # Never built → True
    assert builder.needs_rebuild(ipca) is True

    update_indicator_last_built_at(db_conn, ipca.id, "2026-04-29T08:00:00-03:00")
    update_indicator_last_collected_at(db_conn, ipca.id, "2026-04-29T07:00:00Z")
    fresh = get_indicator_by_code(db_conn, "IPCA")
    # built_at > collected_at → False
    assert builder.needs_rebuild(fresh) is False

    update_indicator_last_collected_at(db_conn, ipca.id, "2026-04-29T09:00:00-03:00")
    fresh2 = get_indicator_by_code(db_conn, "IPCA")
    # collected_at > built_at → True
    assert builder.needs_rebuild(fresh2) is True


def test_build_writes_indicators_index_and_detail(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    result = builder.build(
        db_conn,
        triggered_by="test",
        site_data_dir=data_dir,
        site_charts_dir=charts_dir,
    )

    assert result.status == "success"
    assert "IPCA" in result.changed

    # Index has the spec shape
    index = json.loads((data_dir / "indicators.json").read_text())
    assert "generated_at" in index
    assert set(index["categories"].keys()) == {
        "inflacao", "juros", "correcao_monetaria", "construcao_civil"
    }
    assert index["categories"]["inflacao"]["label"] == "Inflação"
    assert "ipca" in index["categories"]["inflacao"]["indicators"]
    codes = {i["code"] for i in index["indicators"]}
    assert codes == {
        "IPCA", "CDI", "TR", "SELIC", "SELICAC",
        "IGPM", "IGPDI", "INPC", "INCCM", "IPCA15",
    }

    ipca_entry = next(i for i in index["indicators"] if i["code"] == "IPCA")
    assert set(ipca_entry["latest"].keys()) == {"reference_date", "value", "ytd", "last_12m"}

    # Detail JSON for IPCA
    detail = json.loads((data_dir / "ipca.json").read_text())
    assert detail["code"] == "IPCA"
    assert detail["category"] == "inflacao"
    assert detail["source"]["name"] == "Banco Central do Brasil"
    assert detail["meta"]["title"].startswith("IPCA")
    assert detail["unit"] == "percent"
    assert detail["frequency"] == "monthly"
    assert detail["latest"] is not None
    assert set(detail["latest"].keys()) == {
        "reference_date", "value", "ytd", "last_12m", "last_24m"
    }
    # values asc
    refs = [v["reference_date"] for v in detail["values"]]
    assert refs == sorted(refs)
    # last entry is the latest
    assert detail["values"][-1]["reference_date"] == detail["latest"]["reference_date"]
    # full per-value shape
    assert set(detail["values"][0].keys()) == {
        "reference_date", "value", "ytd", "last_12m", "last_24m", "since_inception"
    }
    # charts paths
    assert detail["charts"]["current_year"].endswith(".png")
    assert detail["charts"]["history"].endswith("/ipca-history.png")

    # PNGs exist on disk for the indicator that had data
    png_names = {p.name for p in charts_dir.iterdir()}
    assert "ipca-history.png" in png_names
    assert any(name.startswith("ipca-") and name.endswith(".png") for name in png_names)


def test_build_no_changes_skips_charts(db_conn, site_dirs, monkeypatch):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    # First build
    first = builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    assert first.status == "success"

    # Track chart calls on the second run
    calls = {"current_year": 0, "history": 0}
    real_cy = builder.charts.generate_chart_current_year
    real_hi = builder.charts.generate_chart_history

    def spy_cy(*a, **kw):
        calls["current_year"] += 1
        return real_cy(*a, **kw)

    def spy_hi(*a, **kw):
        calls["history"] += 1
        return real_hi(*a, **kw)

    monkeypatch.setattr(builder.charts, "generate_chart_current_year", spy_cy)
    monkeypatch.setattr(builder.charts, "generate_chart_history", spy_hi)

    second = builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    assert second.status == "no_changes"
    assert second.changed == []
    assert calls == {"current_year": 0, "history": 0}


def test_build_commit_message_format():
    result = builder.BuildResult(
        status="success",
        changed=["IPCA", "CDI"],
        files_generated=8,
        log_id="abc-123",
    )
    msg = builder._build_commit_message(result, today="2026-04-30")
    assert msg.startswith("data: update IPCA, CDI (2026-04-30)\n\n")
    assert "Indicadores atualizados:\n- IPCA\n- CDI" in msg
    assert msg.endswith("Build log: abc-123")


def _git_calls_recorder(porcelain_output: str, *, push_should_fail: bool = False):
    calls: list[list[str]] = []

    def fake_run(args, cwd, check, capture_output, text):  # noqa: ARG001
        calls.append(list(args))
        cmd = args[1] if len(args) > 1 else ""
        if cmd == "status":
            return subprocess.CompletedProcess(args, 0, stdout=porcelain_output, stderr="")
        if cmd == "push" and push_should_fail:
            raise subprocess.CalledProcessError(
                1, args, output="", stderr="remote rejected"
            )
        if cmd == "rev-parse":
            return subprocess.CompletedProcess(
                args, 0, stdout="deadbeefcafebabe1234567890\n", stderr=""
            )
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    return calls, fake_run


def test_deploy_no_changes(db_conn, monkeypatch, tmp_path):
    calls, fake_run = _git_calls_recorder(porcelain_output="")
    monkeypatch.setattr(subprocess, "run", fake_run)

    build_result = builder.BuildResult(
        status="success", changed=["IPCA"], files_generated=4, log_id=None,
    )
    result = builder.deploy(db_conn, build_result, repo_path=tmp_path, triggered_by="cli")

    assert result.status == "no_changes"
    assert result.commit_sha is None
    assert result.pushed is False
    # Apenas o status foi consultado — nem add, commit ou push.
    assert len(calls) == 1
    assert calls[0][1] == "status"


def test_deploy_success(db_conn, monkeypatch, tmp_path):
    porcelain = " M site/data/indicators.json\n M site/data/ipca.json\n"
    calls, fake_run = _git_calls_recorder(porcelain_output=porcelain)
    monkeypatch.setattr(subprocess, "run", fake_run)

    sent: list[tuple] = []

    def fake_send_success(deploy_result, build_result):
        sent.append((deploy_result, build_result))

    monkeypatch.setattr(
        "pipeline.bot.notifications.send_deploy_success", fake_send_success
    )

    # Cria um build_log real para podermos validar update_build_log_commit.
    log_id = start_build_log(db_conn, triggered_by="test")
    finish_build_log(
        db_conn, log_id, status="success",
        indicators_updated=["IPCA"], files_generated=4,
    )
    build_result = builder.BuildResult(
        status="success", changed=["IPCA"], files_generated=4, log_id=log_id,
    )

    result = builder.deploy(db_conn, build_result, repo_path=tmp_path, triggered_by="cli")

    assert result.status == "success"
    assert result.pushed is True
    assert result.commit_sha == "deadbeefcafebabe1234567890"
    assert result.files_changed == [
        "site/data/indicators.json", "site/data/ipca.json",
    ]

    cmds = [c[1] for c in calls]
    assert cmds == ["status", "add", "commit", "push", "rev-parse"]

    # SHA persistido no build_log.
    log = get_last_successful_build(db_conn)
    assert log is not None
    assert log.git_commit_sha == "deadbeefcafebabe1234567890"

    # Notificação disparada com os dois resultados.
    assert len(sent) == 1
    assert sent[0][0] is result
    assert sent[0][1] is build_result


def test_deploy_skips_telegram_notification(db_conn, monkeypatch, tmp_path):
    porcelain = " M data/indicadores.db\n"
    _, fake_run = _git_calls_recorder(porcelain_output=porcelain)
    monkeypatch.setattr(subprocess, "run", fake_run)

    sent: list = []
    monkeypatch.setattr(
        "pipeline.bot.notifications.send_deploy_success",
        lambda *a, **kw: sent.append(a),
    )

    build_result = builder.BuildResult(
        status="success", changed=["IPCA"], files_generated=4, log_id=None,
    )
    result = builder.deploy(
        db_conn, build_result, repo_path=tmp_path, triggered_by="telegram"
    )
    assert result.status == "success"
    # Quando origem é telegram, deploy não notifica o bot (handler já fala com o usuário).
    assert sent == []


def test_deploy_push_failure_notifies_and_reraises(db_conn, monkeypatch, tmp_path):
    porcelain = " M site/data/ipca.json\n"
    _, fake_run = _git_calls_recorder(porcelain_output=porcelain, push_should_fail=True)
    monkeypatch.setattr(subprocess, "run", fake_run)

    errors: list[BaseException] = []
    monkeypatch.setattr(
        "pipeline.bot.notifications.send_deploy_error", lambda exc: errors.append(exc)
    )

    build_result = builder.BuildResult(
        status="success", changed=["IPCA"], files_generated=4, log_id=None,
    )
    with pytest.raises(subprocess.CalledProcessError):
        builder.deploy(db_conn, build_result, repo_path=tmp_path, triggered_by="cli")

    assert len(errors) == 1
    assert "git push" in str(errors[0])


def test_build_logs_recorded(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    log = get_last_successful_build(db_conn)
    assert log is not None
    assert log.status == "success"
    assert "IPCA" in (log.indicators_updated or "")
    assert log.files_generated and log.files_generated > 0


def test_build_writes_groups_json(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    groups_path = data_dir / "groups.json"
    assert groups_path.exists()
    payload = json.loads(groups_path.read_text())
    slugs = {g["slug"] for g in payload["groups"]}
    assert slugs == {
        "inflacao-oficial", "indices-fgv",
        "juros-vs-inflacao", "construcao-civil",
    }
    for g in payload["groups"]:
        assert g["chart"] == f"/charts/compare-{g['slug']}.png"


def test_build_writes_compare_pngs_on_first_run(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    # Os 4 PNGs comparativos devem existir, mesmo que alguns sejam placeholders
    # (ex: INPC sem dados → placeholder, mas arquivo ainda deve estar lá).
    expected = {
        "compare-inflacao-oficial.png",
        "compare-indices-fgv.png",
        "compare-juros-vs-inflacao.png",
        "compare-construcao-civil.png",
    }
    found = {p.name for p in charts_dir.iterdir()}
    assert expected.issubset(found)


def test_build_no_changes_still_ensures_groups_json(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    # Primeiro build: escreve tudo
    first = builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    assert first.status == "success"
    groups_path = data_dir / "groups.json"
    assert groups_path.exists()

    # Apaga groups.json para simular "no_changes" sem o arquivo presente
    groups_path.unlink()

    second = builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    assert second.status == "no_changes"
    # Garante que groups.json foi reescrito mesmo no caminho no_changes
    assert groups_path.exists()
    assert second.files_generated == 1


def test_build_no_changes_keeps_existing_groups_json(db_conn, site_dirs):
    data_dir, charts_dir = site_dirs
    _seed_ipca(db_conn)

    builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    groups_path = data_dir / "groups.json"
    mtime_before = groups_path.stat().st_mtime

    second = builder.build(
        db_conn, triggered_by="test",
        site_data_dir=data_dir, site_charts_dir=charts_dir,
    )
    assert second.status == "no_changes"
    assert second.files_generated == 0
    # Idempotência: arquivo continua existindo, sem reescrita.
    assert groups_path.stat().st_mtime == mtime_before
