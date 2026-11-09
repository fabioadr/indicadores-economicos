"""BCB SGS connector.

Fetches time series from the Sistema Gerenciador de Séries Temporais.
Spec in docs/fase-01/04-connectors.md.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import httpx
from dateutil.relativedelta import relativedelta

from .base import BaseConnector, FetchError, ParseError, RawDataPoint, register

logger = logging.getLogger(__name__)

BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
MAX_WINDOW_YEARS = 5
PAGINATION_PAUSE_SECONDS = 1.0
HTTP_TIMEOUT_SECONDS = 120.0
# httpx 0.28 retries only ConnectError and ConnectTimeout on HTTPTransport.
# The SGS API also returns an empty body or 502/503/504 on a healthy series.
MAX_FETCH_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


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
        for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
            try:
                response = httpx.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            except httpx.TransportError as exc:
                if attempt == MAX_FETCH_ATTEMPTS:
                    raise FetchError(f"Erro HTTP ao buscar série {series_id}: {exc}") from exc
                _backoff(series_id, attempt, f"transporte: {exc}")
                continue

            if response.status_code == 404:
                # BCB returns 404 when there is no data in the requested window
                # (e.g. querying a future month). Treat as empty, not an error.
                return []

            if response.status_code in RETRYABLE_STATUS:
                if attempt == MAX_FETCH_ATTEMPTS:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPError as exc:
                        raise FetchError(
                            f"Erro HTTP ao buscar série {series_id}: {exc}"
                        ) from exc
                _backoff(series_id, attempt, f"HTTP {response.status_code}")
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise FetchError(f"Erro HTTP ao buscar série {series_id}: {exc}") from exc

            try:
                data = response.json()
            except ValueError as exc:
                if attempt == MAX_FETCH_ATTEMPTS:
                    raise ParseError(
                        f"Resposta não-JSON para série {series_id} "
                        f"({_response_hint(response)}): {exc}"
                    ) from exc
                _backoff(series_id, attempt, "corpo vazio ou não-JSON")
                continue

            if not isinstance(data, list):
                raise ParseError(f"Resposta inesperada para série {series_id}: {data!r}")

            return [self._parse_point(item) for item in data]

        raise FetchError(f"Erro HTTP ao buscar série {series_id}: tentativas esgotadas")

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


def _backoff(series_id: int, attempt: int, reason: str) -> None:
    logger.warning(
        "BCB series %s attempt %s/%s failed (%s); retrying",
        series_id,
        attempt,
        MAX_FETCH_ATTEMPTS,
        reason,
    )
    time.sleep(RETRY_BACKOFF_SECONDS * attempt)


def _response_hint(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    preview = response.content[:120].decode("utf-8", errors="replace").replace("\n", " ")
    return f"status={response.status_code} content-type={content_type!r} body={preview!r}"
