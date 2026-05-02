"""Tests for M14 comparison charts and groups.json payload."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pipeline.config_groups import (
    metric_label,
    metric_legend_suffix,
    normalize_group,
)
from pipeline.connectors.base import RawDataPoint
from pipeline.core import comparison_charts
from pipeline.core.aggregations import recompute_aggregations
from pipeline.db.connection import (
    apply_pending_migrations,
    get_connection,
    get_indicator_by_code,
    update_indicator_last_collected_at,
    upsert_value,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "pipeline" / "db" / "migrations"

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def db_conn(tmp_path):
    conn = get_connection(tmp_path / "indicadores.db")
    apply_pending_migrations(conn, MIGRATIONS_DIR)
    yield conn
    conn.close()


def _seed(conn, code: str, *, n: int = 14, base: float = 0.40, step: float = 0.01) -> str:
    ind = get_indicator_by_code(conn, code)
    assert ind is not None, f"seed indicator {code} missing"
    for i in range(n):
        year = 2025 if i < 12 else 2026
        month = (i % 12) + 1
        ref = date(year, month, 1)
        upsert_value(
            conn, ind.id,
            RawDataPoint(reference_date=ref, value=base + step * i, raw_value="x"),
        )
    recompute_aggregations(conn, ind.id)
    update_indicator_last_collected_at(conn, ind.id, "2026-04-29T10:00:00Z")
    return ind.id


def test_normalize_group_accepts_strings_and_objects():
    g = {
        "slug": "x",
        "title": "X",
        "description": "...",
        "indicators": [
            "IPCA",
            {"code": "SELIC", "metric": "value", "style": "step"},
        ],
        "metric": "last_12m",
    }
    norm = normalize_group(g)
    assert norm["indicators"][0] == {"code": "IPCA", "metric": "last_12m", "style": "line"}
    assert norm["indicators"][1] == {"code": "SELIC", "metric": "value", "style": "step"}
    # original not mutated
    assert g["indicators"][0] == "IPCA"


def test_metric_label_known_and_unknown():
    assert metric_label("last_12m") == "Acumulado 12 meses (%)"
    assert metric_label("value") == "Variação no período (%)"
    assert metric_label("unknown_x") == "unknown_x"
    assert metric_legend_suffix("last_12m") == "12m"
    assert metric_legend_suffix("value") == "valor"


def test_generate_comparison_chart_writes_valid_png(db_conn, tmp_path):
    _seed(db_conn, "IPCA")
    _seed(db_conn, "IGPM", base=0.30)
    group = {
        "slug": "test-2",
        "title": "Teste comparativo",
        "description": "...",
        "indicators": ["IPCA", "IGPM"],
        "metric": "last_12m",
    }
    out = tmp_path / "compare-test-2.png"
    ok = comparison_charts.generate_comparison_chart(db_conn, group, out)
    assert ok is True
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_generate_comparison_chart_mixed_metrics_step_and_line(db_conn, tmp_path):
    _seed(db_conn, "IPCA")
    _seed(db_conn, "SELIC", base=10.0, step=0.05)
    group = {
        "slug": "test-mixed",
        "title": "SELIC vs IPCA",
        "description": "...",
        "indicators": [
            {"code": "IPCA", "metric": "last_12m"},
            {"code": "SELIC", "metric": "value", "style": "step"},
        ],
        "metric": "last_12m",
    }
    out = tmp_path / "compare-test-mixed.png"
    ok = comparison_charts.generate_comparison_chart(db_conn, group, out)
    assert ok is True
    assert out.read_bytes()[:8] == PNG_HEADER


def test_generate_comparison_chart_all_null_returns_false_and_writes_placeholder(
    db_conn, tmp_path
):
    # IPCA seeded with apenas 3 pontos → last_12m fica None em todos.
    _seed(db_conn, "IPCA", n=3)
    group = {
        "slug": "test-empty",
        "title": "Vazio",
        "description": "...",
        "indicators": ["IPCA"],
        "metric": "last_12m",
    }
    out = tmp_path / "compare-test-empty.png"
    ok = comparison_charts.generate_comparison_chart(db_conn, group, out)
    assert ok is False
    # Placeholder ainda é um PNG válido
    assert out.exists()
    assert out.read_bytes()[:8] == PNG_HEADER


def test_build_groups_payload_aligns_latest_common_date(db_conn, tmp_path):
    # IPCA com 14 pontos (último em 2026-02-01)
    _seed(db_conn, "IPCA", n=14)
    # IGPM com 13 pontos (último em 2026-01-01) — last_12m só a partir do 12º
    _seed(db_conn, "IGPM", n=13, base=0.20)

    groups = [
        {
            "slug": "g",
            "title": "G",
            "description": "...",
            "indicators": ["IPCA", "IGPM"],
            "metric": "last_12m",
        }
    ]
    payload = comparison_charts.build_groups_payload(
        db_conn, groups, "2026-04-29T12:00:00-03:00",
    )
    assert payload["generated_at"] == "2026-04-29T12:00:00-03:00"
    assert len(payload["groups"]) == 1
    g0 = payload["groups"][0]
    assert g0["chart"] == "/charts/compare-g.png"
    # common_date: last_12m em IPCA aparece a partir de 2025-12-01 (12º ponto);
    # IGPM tem last_12m apenas no 12º (2025-12-01) e 13º (2026-01-01).
    # Mínimo dos máximos = 2026-01-01 (último de IGPM).
    assert g0["latest"]["reference_date"] == "2026-01-01"
    # ambos os codes aparecem em latest.values
    assert set(g0["latest"]["values"].keys()) == {"IPCA", "IGPM"}
    # campos completos
    assert "value" in g0["latest"]["values"]["IPCA"]
    assert "last_12m" in g0["latest"]["values"]["IPCA"]
    # indicators normalizados
    codes = [i["code"] for i in g0["indicators"]]
    assert codes == ["IPCA", "IGPM"]


def test_build_groups_payload_empty_when_one_indicator_missing_data(db_conn):
    # IPCA seeded, INPC vazio
    _seed(db_conn, "IPCA")
    groups = [
        {
            "slug": "g",
            "title": "G",
            "description": "...",
            "indicators": ["IPCA", "INPC"],
            "metric": "last_12m",
        }
    ]
    payload = comparison_charts.build_groups_payload(
        db_conn, groups, "2026-04-29T12:00:00-03:00",
    )
    g0 = payload["groups"][0]
    # common_date é None porque INPC não tem dados
    assert g0["latest"]["reference_date"] is None
    assert g0["latest"]["values"] == {}
