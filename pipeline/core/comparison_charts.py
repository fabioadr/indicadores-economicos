"""PNGs comparativos entre indicadores e payload de `site/data/groups.json`.

Spec: docs/fase-02/05-site-features.md (Parte B).

Cada grupo definido em `pipeline.config_groups.INDICATOR_GROUPS` produz:
- 1 PNG `compare-{slug}.png` em `site/public/charts/`.
- 1 entrada em `site/data/groups.json` com indicadores enriquecidos e
  últimos valores no horizonte comum mais recente.

A paleta multi-linha é local (uma cor por linha). A paleta por categoria de
`charts.py` colapsaria múltiplos índices de inflação numa mesma cor.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from pipeline.config_groups import (
    metric_label,
    metric_legend_suffix,
    normalize_group,
)
from pipeline.core import charts as base_charts
from pipeline.db.connection import (
    Indicator,
    IndicatorValue,
    get_indicator_by_code,
    list_values,
)

logger = logging.getLogger(__name__)

PALETTE = ["#1E3A8A", "#B91C1C", "#166534", "#92400E", "#581C87"]

FIGSIZE = (12.0, 6.0)
DPI = 100


def _series_for_item(
    conn: sqlite3.Connection, item: dict
) -> tuple[Indicator | None, list[tuple[date, float]]]:
    """Retorna (Indicator, [(date, value), ...]) filtrado por métrica não-nula."""
    ind = get_indicator_by_code(conn, item["code"])
    if ind is None:
        return None, []
    values = list_values(conn, ind.id, order="asc")
    metric = item["metric"]
    points: list[tuple[date, float]] = []
    for v in values:
        m = getattr(v, metric, None)
        if m is None:
            continue
        points.append((v.reference_date, m))
    return ind, points


def generate_comparison_chart(
    conn: sqlite3.Connection, group: dict, out_path: Path
) -> bool:
    """Gera o PNG comparativo do grupo. Retorna True se ao menos uma linha foi plotada.

    Indicadores sem dados (todos `None` na métrica) são ignorados na legenda.
    Se nenhum indicador rendeu pontos, escreve um placeholder vazio e retorna False.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    g = normalize_group(group)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    plotted = 0
    metrics_used: set[str] = set()
    for idx, item in enumerate(g["indicators"]):
        ind, points = _series_for_item(conn, item)
        if ind is None or not points:
            logger.info(
                "comparison: skipping %s (no data for metric=%s)",
                item["code"], item["metric"],
            )
            continue
        dates_, values_ = zip(*points, strict=False)
        color = PALETTE[idx % len(PALETTE)]
        label = f"{ind.code} ({metric_legend_suffix(item['metric'])})"
        if item["style"] == "step":
            ax.step(dates_, values_, where="post", color=color, linewidth=2.0, label=label)
        else:
            ax.plot(dates_, values_, color=color, linewidth=2.0, label=label)
        plotted += 1
        metrics_used.add(item["metric"])

    if plotted == 0:
        plt.close(fig)
        base_charts._save_empty(out_path, group["title"])
        return False

    if len(metrics_used) == 1:
        ax.set_ylabel(metric_label(next(iter(metrics_used))))
    else:
        ax.set_ylabel("% (ver legenda)")

    ax.set_title(group["title"], fontsize=14, pad=16)
    ax.legend(loc="best", frameon=False)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    base_charts._style_axes(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, format="png", facecolor="white")
    plt.close(fig)
    return True


def _find_latest_common_date(
    conn: sqlite3.Connection, group: dict
) -> date | None:
    """Mínimo dos máximos de reference_date entre os indicadores do grupo,
    considerando a métrica de cada item (datas onde `metric` não é None)."""
    g = normalize_group(group)
    latest_per_indicator: list[date] = []
    for item in g["indicators"]:
        _ind, points = _series_for_item(conn, item)
        if not points:
            return None
        latest_per_indicator.append(points[-1][0])
    if not latest_per_indicator:
        return None
    return min(latest_per_indicator)


def _value_at(
    conn: sqlite3.Connection, indicator_id: str, target: date
) -> IndicatorValue | None:
    """Pega o IndicatorValue mais recente com reference_date <= target."""
    values = list_values(conn, indicator_id, order="asc")
    chosen: IndicatorValue | None = None
    for v in values:
        if v.reference_date <= target:
            chosen = v
        else:
            break
    return chosen


def build_groups_payload(
    conn: sqlite3.Connection,
    groups: list[dict],
    generated_at: str,
    *,
    charts_url_prefix: str = "/charts",
) -> dict:
    """Monta o dict serializável para `site/data/groups.json`."""
    enriched: list[dict] = []
    for group in groups:
        g = normalize_group(group)
        items_full: list[dict] = []
        latest_values: dict[str, dict] = {}
        common_date = _find_latest_common_date(conn, group)

        for item in g["indicators"]:
            ind = get_indicator_by_code(conn, item["code"])
            if ind is None:
                continue
            items_full.append(
                {
                    "code": ind.code,
                    "slug": ind.slug,
                    "name": ind.name,
                    "metric": item["metric"],
                    "style": item["style"],
                }
            )
            if common_date is not None:
                v = _value_at(conn, ind.id, common_date)
                if v is not None:
                    latest_values[ind.code] = {
                        "reference_date": v.reference_date.isoformat(),
                        "value": v.value,
                        "last_12m": v.last_12m,
                        "ytd": v.ytd,
                        "last_24m": v.last_24m,
                    }

        enriched.append(
            {
                "slug": g["slug"],
                "title": g["title"],
                "description": g["description"],
                "metric": g.get("metric", "last_12m"),
                "indicators": items_full,
                "chart": f"{charts_url_prefix}/compare-{g['slug']}.png",
                "latest": {
                    "reference_date": (
                        common_date.isoformat() if common_date else None
                    ),
                    "values": latest_values,
                },
            }
        )

    return {"generated_at": generated_at, "groups": enriched}
