"""Static PNG charts for indicator pages.

Spec: docs/05-pipeline.md (1200x600 @ 100 dpi, white background, no seaborn)
and docs/06-site.md (palette by category).

Modos especiais (alinhados com `indicators.aggregation_mode`):

- ``compound_monthly`` (default): barras mensais + linha YTD no anual; linha
  mensal + linha 12m no histórico.
- ``compound_daily_to_monthly``: a série tem múltiplos valores por mês (ex:
  TR diária). Reduzimos ao último valor de cada mês antes de plotar — assim
  a granularidade visual passa a ser mensal, igual aos demais.
- ``none``: a série não admite composição (ex: SELIC anualizada). Plotamos
  apenas uma linha de "taxa em vigor" — sem barras mensais, sem YTD.
- ``level``: série de nível absoluto (R$ mi / índice). Plotamos a série do
  nível; no histórico, opcionalmente a variação YoY (%).
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
    "construcao_civil": "#c2410c",
    "poupanca": "#0f766e",
    "mercado_imobiliario": "#7c2d12",
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


def _last_per_month(values: list[IndicatorValue]) -> list[IndicatorValue]:
    """Mantém apenas o último valor de cada (ano, mês), preservando a ordem."""
    by_month: dict[tuple[int, int], IndicatorValue] = {}
    for v in values:
        key = (v.reference_date.year, v.reference_date.month)
        by_month[key] = v
    return sorted(by_month.values(), key=lambda v: v.reference_date)


def _style_axes(ax) -> None:
    ax.axhline(0, color=AXIS_COLOR, linewidth=0.8)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, color=GRID_COLOR)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save_empty(out_path: Path, year_or_title: str) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_title(year_or_title)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, format="png", facecolor="white")
    plt.close(fig)


def generate_chart_current_year(
    values: list[IndicatorValue],
    category: str,
    year: int,
    out_path: Path,
    *,
    aggregation_mode: str = "compound_monthly",
) -> None:
    """Bars per month + YTD cumulative line for the given year.

    Comportamento por modo:

    - ``compound_monthly``: barras mensais + linha YTD calculada por composição.
    - ``compound_daily_to_monthly``: reduz a 1 valor por mês (último do mês) antes
      de plotar — assim TR diária fica visualmente igual aos mensais.
    - ``none``: linha contínua da "taxa em vigor" (sem barras, sem YTD).
    - ``level``: linha do nível absoluto no ano (sem linha de acumulado).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    color = _category_color(category)

    year_values = [v for v in values if v.reference_date.year == year]

    if aggregation_mode == "none":
        fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        if year_values:
            xs = [v.reference_date for v in year_values]
            ys = [v.value for v in year_values]
            ax.plot(
                xs, ys, color=color, linewidth=2.0, marker="o",
                label="Taxa em vigor (% a.a.)",
            )
            ax.legend(loc="best", frameon=False)
        ax.set_title(str(year))
        _style_axes(ax)
        fig.tight_layout()
        fig.savefig(out_path, format="png", facecolor="white")
        plt.close(fig)
        return

    if aggregation_mode == "level":
        fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        if year_values:
            months = [v.reference_date.month for v in year_values]
            levels = [v.value for v in year_values]
            ax.plot(
                months, levels, color=color, linewidth=2.0, marker="o",
                label="Nível",
            )
            ax.legend(loc="best", frameon=False)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MONTH_LABELS)
        ax.set_xlim(0.5, 12.5)
        ax.set_title(str(year))
        _style_axes(ax)
        fig.tight_layout()
        fig.savefig(out_path, format="png", facecolor="white")
        plt.close(fig)
        return

    if aggregation_mode == "compound_daily_to_monthly":
        year_values = _last_per_month(year_values)

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
    *,
    aggregation_mode: str = "compound_monthly",
) -> None:
    """Monthly line + 12m cumulative line over the entire series.

    Para ``aggregation_mode='none'`` plota apenas uma linha da taxa em vigor.
    Para ``compound_daily_to_monthly`` reduz a 1 valor por mês antes de plotar.
    Para ``level`` plota o nível e, se disponível, a variação YoY (%).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    color = _category_color(category)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    if aggregation_mode == "none":
        if values:
            dates = [v.reference_date for v in values]
            monthly = [v.value for v in values]
            ax.plot(
                dates, monthly, color=color, linewidth=1.6,
                label="Taxa em vigor (% a.a.)",
            )
            ax.legend(loc="best", frameon=False)
        _style_axes(ax)
        fig.tight_layout()
        fig.savefig(out_path, format="png", facecolor="white")
        plt.close(fig)
        return

    if aggregation_mode == "level":
        if values:
            dates = [v.reference_date for v in values]
            levels = [v.value for v in values]
            ax.plot(dates, levels, color=color, linewidth=1.6, label="Nível")
            yoy = [v.last_12m for v in values]
            if any(y is not None for y in yoy):
                ax2 = ax.twinx()
                ax2.plot(
                    dates, yoy, color=ACCUM_COLOR, linewidth=1.2,
                    alpha=0.8, label="Var. 12m (%)",
                )
                ax2.spines["top"].set_visible(False)
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc="best", frameon=False)
            else:
                ax.legend(loc="best", frameon=False)
        _style_axes(ax)
        fig.tight_layout()
        fig.savefig(out_path, format="png", facecolor="white")
        plt.close(fig)
        return

    plot_values = (
        _last_per_month(values)
        if aggregation_mode == "compound_daily_to_monthly"
        else values
    )

    if plot_values:
        dates = [v.reference_date for v in plot_values]
        monthly = [v.value for v in plot_values]
        last_12m = [v.last_12m for v in plot_values]
        ax.plot(dates, monthly, color=color, linewidth=1.2, alpha=0.7, label="Mensal (%)")
        ax.plot(dates, last_12m, color=ACCUM_COLOR, linewidth=1.6, label="Acumulado 12m (%)")
        ax.legend(loc="best", frameon=False)

    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out_path, format="png", facecolor="white")
    plt.close(fig)
