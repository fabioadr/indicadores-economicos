"""Tests for pipeline/bot/formatters: pure message templates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

from pipeline.bot import formatters
from pipeline.core.builder import BuildResult, DeployResult
from pipeline.core.scheduler import CollectResult


@dataclass
class _Indicator:
    id: str = "ind-1"
    code: str = "IPCA"
    slug: str = "ipca"
    name: str = "IPCA"
    category: str = "inflacao"
    frequency: str = "monthly"
    last_collected_at: str | None = "2026-04-28T07:15:00Z"


@dataclass
class _Value:
    reference_date: date = date(2026, 3, 1)
    value: float = 0.56


@dataclass
class _BuildLog:
    finished_at: str | None = "2026-04-28T07:15:00Z"
    indicators_updated: str | None = "IPCA,CDI"


def test_help_message_lists_commands():
    msg = formatters.help_message()
    for cmd in ("/status", "/indicadores", "/coletar", "/publicar", "/logs", "/erros"):
        assert cmd in msg


def test_status_message_with_data():
    msg = formatters.status_message(
        active_count=3, last_build=_BuildLog(), errors_24h=0
    )
    assert "Indicadores ativos: 3" in msg
    assert "2 atualizações" in msg
    assert "Erros nas últimas 24h: 0" in msg


def test_status_message_without_build():
    msg = formatters.status_message(
        active_count=3, last_build=None, errors_24h=2
    )
    assert "Último deploy: —" in msg
    assert "Erros nas últimas 24h: 2" in msg


def test_indicators_message_empty():
    assert "Nenhum indicador" in formatters.indicators_message([], {})


def test_indicators_message_with_latest():
    ind = _Indicator()
    msg = formatters.indicators_message([ind], {"ind-1": _Value()})
    assert "IPCA" in msg
    assert "0,56%" in msg
    assert "mar/2026" in msg


def test_collect_result_success():
    result = CollectResult(code="IPCA", added=1, updated=0)
    msg = formatters.collect_result_message(result, _Value())
    assert "IPCA" in msg
    assert "0,56%" in msg
    assert "/publicar" in msg


def test_collect_result_no_changes():
    result = CollectResult(code="IPCA", added=0, updated=0)
    msg = formatters.collect_result_message(result, None)
    assert "já está atualizado" in msg


def test_collect_result_error():
    result = CollectResult(code="IPCA", added=0, updated=0, error="HTTP 503")
    msg = formatters.collect_result_message(result, None)
    assert "❌" in msg
    assert "HTTP 503" in msg


def test_collect_summary_mixed():
    results = [
        CollectResult(code="IPCA", added=1, updated=0),
        CollectResult(code="CDI", added=0, updated=0),
        CollectResult(code="TR", added=0, updated=0, error="boom"),
    ]
    msg = formatters.collect_summary_message(results)
    assert "IPCA" in msg and "+1 novo" in msg
    assert "CDI: sem mudanças" in msg
    assert "TR" in msg and "boom" in msg
    assert "/erros" in msg
    assert "/publicar" in msg


def test_collect_error_message_contains_code():
    msg = formatters.collect_error_message(_Indicator(), "HTTP 503")
    assert "IPCA" in msg
    assert "HTTP 503" in msg
    assert "/coletar IPCA" in msg


def test_build_success_message():
    result = BuildResult("success", ["IPCA", "CDI"], 6, "log-1")
    msg = formatters.build_success_message(result)
    assert "IPCA" in msg and "CDI" in msg
    # M9 já implementado — deploy mention removido daqui (vai em deploy_success_message).
    assert "M9" not in msg
    assert "Build concluído" in msg


def test_build_error_message():
    msg = formatters.build_error_message(RuntimeError("disk full"))
    assert "RuntimeError" in msg
    assert "disk full" in msg


def test_deploy_success_message():
    build = BuildResult("success", ["IPCA", "CDI"], 6, "log-1")
    deploy = DeployResult(
        status="success",
        commit_sha="abcdef0123456789",
        files_changed=["site/data/ipca.json"],
        pushed=True,
    )
    msg = formatters.deploy_success_message(deploy, build)
    assert "Deploy concluído" in msg
    assert "IPCA, CDI" in msg
    assert "abcdef0" in msg  # SHA encurtado em 7 chars
    assert "indicadoreseconomicoshoje.com.br" in msg


def test_deploy_error_message():
    msg = formatters.deploy_error_message(RuntimeError("git push falhou: remote rejected"))
    assert "ERRO no deploy" in msg
    assert "remote rejected" in msg


def test_publish_summary_message_no_changes_in_build():
    build = BuildResult("no_changes", [], 0, None)
    msg = formatters.publish_summary_message(build, None)
    assert "Nenhum indicador" in msg


def test_publish_summary_message_no_changes_in_deploy():
    build = BuildResult("success", ["IPCA"], 4, "log-1")
    deploy = DeployResult(status="no_changes")
    msg = formatters.publish_summary_message(build, deploy)
    assert "Build concluído" in msg
    assert "Working tree limpo" in msg


def test_publish_summary_message_full_success():
    build = BuildResult("success", ["IPCA"], 4, "log-1")
    deploy = DeployResult(
        status="success", commit_sha="0123456789abcdef", files_changed=["x"], pushed=True,
    )
    msg = formatters.publish_summary_message(build, deploy)
    assert "Deploy concluído" in msg
    assert "0123456" in msg


def test_logs_message_empty():
    assert formatters.logs_message([]) == "📭 Sem logs ainda."


def test_errors_message_empty():
    assert formatters.errors_message([]) == "✅ Sem erros nas últimas 24h."


def test_unauthorized_message():
    assert formatters.unauthorized_message() == "⛔ Não autorizado."
