"""BCB SGS connector.

Fetches time series from the Sistema Gerenciador de Séries Temporais.
Spec in docs/04-connectors.md.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import httpx
from dateutil.relativedelta import relativedelta

from .base import BaseConnector, FetchError, ParseError, RawDataPoint, register

BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
MAX_WINDOW_YEARS = 10
PAGINATION_PAUSE_SECONDS = 1.0
HTTP_TIMEOUT_SECONDS = 30.0


@register("bcb_sgs")
class BCBSGSConnector(BaseConnector):
    """Connector for the BCB Sistema Gerenciador de Séries Temporais (SGS)."""

    def fetch(
        self,
        config: dict[str, Any],
        since: date | None = None,
        until: date | None = None,
    ) -> list[RawDataPoint]:
        series_id = config["series_id"]
        until = until or date.today()
        since = since or self._earliest_default()

        all_points: list[RawDataPoint] = []
        windows = list(self._windows(since, until))
        for i, (window_start, window_end) in enumerate(windows):
            all_points.extend(self._fetch_window(series_id, window_start, window_end))
            if i < len(windows) - 1:
                time.sleep(PAGINATION_PAUSE_SECONDS)

        seen: set[date] = set()
        unique: list[RawDataPoint] = []
        for p in sorted(all_points, key=lambda x: x.reference_date):
            if p.reference_date not in seen:
                seen.add(p.reference_date)
                unique.append(p)
        return unique

    def _windows(self, since: date, until: date) -> Iterator[tuple[date, date]]:
        cursor = since
        while cursor <= until:
            window_end = min(
                cursor + relativedelta(years=MAX_WINDOW_YEARS) - timedelta(days=1),
                until,
            )
            yield cursor, window_end
            cursor = window_end + timedelta(days=1)

    def _fetch_window(self, series_id: int, start: date, end: date) -> list[RawDataPoint]:
        url = BCB_BASE_URL.format(series_id=series_id)
        params = {
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        }
        try:
            response = httpx.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            if response.status_code == 404:
                # BCB returns 404 when there is no data in the requested window
                # (e.g. querying a future month). Treat as empty, not an error.
                return []
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise FetchError(f"Erro HTTP ao buscar série {series_id}: {e}") from e

        try:
            data = response.json()
        except ValueError as e:
            raise ParseError(f"Resposta não-JSON para série {series_id}: {e}") from e

        if not isinstance(data, list):
            raise ParseError(f"Resposta inesperada para série {series_id}: {data!r}")

        return [self._parse_point(item) for item in data]

    def _parse_point(self, item: dict[str, Any]) -> RawDataPoint:
        try:
            reference_date = self._parse_date(item["data"])
            raw = item["valor"]
            value = float(str(raw).replace(",", "."))
        except (KeyError, TypeError, ValueError) as e:
            raise ParseError(f"Item inválido: {item} ({e})") from e
        return RawDataPoint(
            reference_date=reference_date,
            value=value,
            raw_value=str(raw),
        )

    def _parse_date(self, s: str) -> date:
        d, m, y = s.split("/")
        return date(int(y), int(m), int(d))

    def _earliest_default(self) -> date:
        return date(1986, 1, 1)
