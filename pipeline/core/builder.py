"""Generate site/data/*.json + site/public/charts/*.png from SQLite.

Spec: docs/05-pipeline.md.

JSONs are always rewritten (cheap). Charts are regenerated only for indicators
whose `last_collected_at` is newer than `last_built_at` (or that never built).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline import config
from pipeline.core import charts
from pipeline.db.connection import (
    Indicator,
    IndicatorValue,
    finish_build_log,
    list_active_indicators,
    list_values,
    start_build_log,
    update_indicator_last_built_at,
)

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "inflacao": "Inflação",
    "juros": "Juros",
    "correcao_monetaria": "Correção Monetária",
}

SP_TZ = ZoneInfo("America/Sao_Paulo")


@dataclass
class BuildResult:
    status: str  # "success" | "no_changes" | "error"
    changed: list[str]
    files_generated: int
    log_id: str | None


def _now_sp_iso() -> str:
    ts = datetime.now(tz=SP_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    return ts[:-2] + ":" + ts[-2:]


def _value_full_dict(v: IndicatorValue) -> dict:
    return {
        "reference_date": v.reference_date.isoformat(),
        "value": v.value,
        "ytd": v.ytd,
        "last_12m": v.last_12m,
        "last_24m": v.last_24m,
        "since_inception": v.since_inception,
    }


def _latest_index(v: IndicatorValue) -> dict:
    return {
        "reference_date": v.reference_date.isoformat(),
        "value": v.value,
        "ytd": v.ytd,
        "last_12m": v.last_12m,
    }


def _latest_detail(v: IndicatorValue) -> dict:
    return {
        "reference_date": v.reference_date.isoformat(),
        "value": v.value,
        "ytd": v.ytd,
        "last_12m": v.last_12m,
        "last_24m": v.last_24m,
    }


def _parse_iso(ts: str) -> datetime:
    # Accept both "...Z" (UTC) and offset-aware "...+HH:MM" forms.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def needs_rebuild(ind: Indicator) -> bool:
    if ind.last_built_at is None:
        return True
    if ind.last_collected_at is None:
        return False
    return _parse_iso(ind.last_collected_at) > _parse_iso(ind.last_built_at)


def _build_categories(indicators: list[Indicator]) -> dict:
    grouped: dict[str, list[str]] = defaultdict(list)
    for ind in indicators:
        grouped[ind.category].append(ind.slug)

    out: dict[str, dict] = {}
    for cat, slugs in grouped.items():
        out[cat] = {
            "label": CATEGORY_LABELS.get(cat, cat),
            "indicators": sorted(slugs),
        }
    return out


def write_indicators_index(
    indicators: list[Indicator],
    latest_by_id: dict[str, IndicatorValue | None],
    out_dir: Path,
    generated_at: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": generated_at,
        "categories": _build_categories(indicators),
        "indicators": [
            {
                "code": ind.code,
                "slug": ind.slug,
                "name": ind.name,
                "category": ind.category,
                "frequency": ind.frequency,
                "latest": (
                    _latest_index(latest_by_id[ind.id])
                    if latest_by_id.get(ind.id) is not None
                    else None
                ),
            }
            for ind in indicators
        ],
    }
    out_path = out_dir / "indicators.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_indicator_detail(
    ind: Indicator,
    values: list[IndicatorValue],
    out_dir: Path,
    charts_url_prefix: str,
    last_built_at: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = values[-1] if values else None
    payload = {
        "code": ind.code,
        "slug": ind.slug,
        "name": ind.name,
        "short_description": ind.short_description,
        "long_description": ind.long_description,
        "category": ind.category,
        "unit": ind.unit,
        "frequency": ind.frequency,
        "source": {
            "name": ind.source_name,
            "url": ind.source_url,
        },
        "meta": {
            "title": ind.meta_title,
            "description": ind.meta_description,
        },
        "latest": _latest_detail(latest) if latest else None,
        "values": [_value_full_dict(v) for v in values],
        "charts": {
            "current_year": f"{charts_url_prefix}/{ind.slug}-{_current_year()}.png",
            "history": f"{charts_url_prefix}/{ind.slug}-history.png",
        },
        "last_built_at": last_built_at,
    }
    out_path = out_dir / f"{ind.slug}.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def _current_year() -> int:
    return datetime.now(tz=SP_TZ).year


def build(
    conn: sqlite3.Connection,
    *,
    triggered_by: str = "cli",
    site_data_dir: Path | None = None,
    site_charts_dir: Path | None = None,
    charts_url_prefix: str = "/charts",
) -> BuildResult:
    data_dir = site_data_dir or config.SITE_DATA_DIR
    charts_dir = site_charts_dir or config.SITE_CHARTS_DIR

    log_id = start_build_log(conn, triggered_by)
    try:
        indicators = list_active_indicators(conn)
        if not indicators:
            finish_build_log(
                conn, log_id, status="no_changes",
                indicators_updated=[], files_generated=0,
            )
            return BuildResult("no_changes", [], 0, log_id)

        changed = [ind for ind in indicators if needs_rebuild(ind)]
        if not changed:
            finish_build_log(
                conn, log_id, status="no_changes",
                indicators_updated=[], files_generated=0,
            )
            logger.info("build: no indicators need rebuild")
            return BuildResult("no_changes", [], 0, log_id)

        generated_at = _now_sp_iso()
        year = _current_year()

        values_by_id: dict[str, list[IndicatorValue]] = {
            ind.id: list_values(conn, ind.id, order="asc") for ind in indicators
        }
        latest_by_id: dict[str, IndicatorValue | None] = {
            ind.id: (values_by_id[ind.id][-1] if values_by_id[ind.id] else None)
            for ind in indicators
        }

        files_generated = 0

        index_path = write_indicators_index(
            indicators, latest_by_id, data_dir, generated_at
        )
        files_generated += 1
        logger.info("build: wrote %s", index_path)

        for ind in indicators:
            detail_path = write_indicator_detail(
                ind,
                values_by_id[ind.id],
                data_dir,
                charts_url_prefix,
                generated_at,
            )
            files_generated += 1
            logger.info("build: wrote %s", detail_path)

        for ind in changed:
            vals = values_by_id[ind.id]
            cy_path = charts_dir / f"{ind.slug}-{year}.png"
            hi_path = charts_dir / f"{ind.slug}-history.png"
            charts.generate_chart_current_year(vals, ind.category, year, cy_path)
            charts.generate_chart_history(vals, ind.category, hi_path)
            files_generated += 2
            logger.info("build: charts %s, %s", cy_path, hi_path)
            update_indicator_last_built_at(conn, ind.id, generated_at)

        changed_codes = [ind.code for ind in changed]
        finish_build_log(
            conn, log_id, status="success",
            indicators_updated=changed_codes,
            files_generated=files_generated,
        )
        result = BuildResult("success", changed_codes, files_generated, log_id)
        if triggered_by != "telegram":
            try:
                from pipeline.bot import notifications

                notifications.send_build_success(result)
            except Exception:  # noqa: BLE001
                logger.exception("Falha ao notificar sucesso de build")
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("build failed")
        finish_build_log(
            conn, log_id, status="error", error_message=str(exc),
        )
        if triggered_by != "telegram":
            try:
                from pipeline.bot import notifications

                notifications.send_build_error(exc)
            except Exception:  # noqa: BLE001
                logger.exception("Falha ao notificar erro de build")
        raise
