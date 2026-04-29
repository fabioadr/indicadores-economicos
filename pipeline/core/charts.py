"""Static PNG charts for indicator pages.

Spec: docs/05-pipeline.md (1200x600 @ 100 dpi, white background, no seaborn)
and docs/06-site.md (palette by category).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from pipeline.db.connection import IndicatorValue  # noqa: E402

PALETTE = {
    "inflacao": "#b91c1c",
    "juros": "#1e3a8a",
    "correcao_monetaria": "#166534",
}
DEFAULT_COLOR = "#1a1a1a"
ACCUM_COLOR = "#525252"
GRID_COLOR = "#e5e5e0"
AXIS_COLOR = "#a3a3a3"

FIGSIZE = (12.0, 6.0)
DPI = 100

MONTH_LABELS = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]


def _category_color(category: str) -> str:
    return PALETTE.get(category, DEFAULT_COLOR)


def _accumulate_running(values: list[float]) -> list[float]:
    factor = 1.0
    out: list[float] = []
    for v in values:
        factor *= 1 + v / 100
        out.append((factor - 1) * 100)
    return out


def _style_axes(ax) -> None:
    ax.axhline(0, color=AXIS_COLOR, linewidth=0.8)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, color=GRID_COLOR)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def generate_chart_current_year(
    values: list[IndicatorValue],
    category: str,
    year: int,
    out_path: Path,
) -> None:
    """Bars per month + YTD cumulative line for the given year."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    color = _category_color(category)

    year_values = [v for v in values if v.reference_date.year == year]
    months = [v.reference_date.month for v in year_values]
    monthly = [v.value for v in year_values]
    ytd = _accumulate_running(monthly)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    if monthly:
        ax.bar(months, monthly, color=color, alpha=0.85, label="Mensal (%)")
        ax.plot(
            months, ytd, color=ACCUM_COLOR, linewidth=2.0, marker="o",
            label="Acumulado YTD (%)",
        )

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlim(0.5, 12.5)
    ax.set_title(str(year))
    _style_axes(ax)
    if monthly:
        ax.legend(loc="best", frameon=False)

    fig.tight_layout()
    fig.savefig(out_path, format="png", facecolor="white")
    plt.close(fig)


def generate_chart_history(
    values: list[IndicatorValue],
    category: str,
    out_path: Path,
) -> None:
    """Monthly line + 12m cumulative line over the entire series."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    color = _category_color(category)

    dates = [v.reference_date for v in values]
    monthly = [v.value for v in values]
    last_12m = [v.last_12m for v in values]

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    if dates:
        ax.plot(dates, monthly, color=color, linewidth=1.2, alpha=0.7, label="Mensal (%)")
        ax.plot(dates, last_12m, color=ACCUM_COLOR, linewidth=1.6, label="Acumulado 12m (%)")
        ax.legend(loc="best", frameon=False)

    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, format="png", facecolor="white")
    plt.close(fig)
