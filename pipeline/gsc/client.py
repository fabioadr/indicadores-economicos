"""Cliente HTTP da Search Console API v3 (searchanalytics + sites.list)."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote

import httpx

from pipeline.gsc.auth import fetch_access_token
from pipeline.gsc.exceptions import GscAuthError, GscFetchError

SEARCH_ANALYTICS_URL = (
    "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
)
SITES_URL = "https://www.googleapis.com/webmasters/v3/sites"
ROW_LIMIT = 25_000
_MAX_RETRIES = 3
_RETRY_STATUSES = frozenset({429, 500, 502, 503})


@dataclass(frozen=True)
class GscRow:
    keys: tuple[str, ...]
    clicks: float
    impressions: float
    ctr: float
    position: float


@dataclass(frozen=True)
class GscSite:
    site_url: str
    permission_level: str


class GscClient:
    """POST searchanalytics.query + GET sites, autenticado com Bearer."""

    def __init__(
        self,
        site_url: str,
        *,
        credentials_path: Path | None = None,
        token: str | None = None,
        http: httpx.Client | None = None,
        data_state: str = "final",
    ) -> None:
        if not site_url:
            raise GscFetchError("site_url vazio")
        self.site_url = site_url
        self._credentials_path = credentials_path
        self._token = token
        self._http = http
        self.data_state = data_state
        self._owns_http = http is None

    def close(self) -> None:
        if self._owns_http and self._http is not None:
            self._http.close()
            self._http = None

    def __enter__(self) -> GscClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=60)
        return self._http

    def _bearer(self) -> str:
        if self._token is None:
            if self._credentials_path is None:
                raise GscAuthError("Nem token nem GSC_CREDENTIALS_PATH")
            self._token = fetch_access_token(
                self._credentials_path, http=self._client()
            )
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._bearer()}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None
        refreshed = False
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client().request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_body,
                )
            except httpx.HTTPError as exc:
                last_error = GscFetchError(f"Erro de rede GSC: {exc}")
                time.sleep(2**attempt)
                continue
            if response.status_code == 401 and not refreshed:
                self._token = None
                refreshed = True
                continue
            if response.status_code == 403:
                raise GscAuthError(
                    "403 da Search Console API — a service account precisa ser "
                    "adicionada como usuário na propriedade GSC (não só no IAM "
                    "do GCP). Ver docs/gsc/SETUP.md."
                )
            if response.status_code in _RETRY_STATUSES:
                time.sleep(2**attempt)
                last_error = GscFetchError(
                    f"GSC HTTP {response.status_code}: {response.text[:300]}"
                )
                continue
            if response.status_code >= 400:
                raise GscFetchError(
                    f"GSC HTTP {response.status_code}: {response.text[:300]}"
                )
            return response
        raise last_error or GscFetchError("GSC: retries esgotados")

    def list_sites(self) -> list[GscSite]:
        response = self._request("GET", SITES_URL)
        entries = response.json().get("siteEntry") or []
        return [
            GscSite(
                permission_level=str(entry.get("permissionLevel") or ""),
                site_url=str(entry.get("siteUrl") or ""),
            )
            for entry in entries
        ]

    def query(
        self,
        start: date,
        end: date,
        dimensions: Sequence[str],
        *,
        dimension_filters: list[dict] | None = None,
    ) -> list[GscRow]:
        encoded_site = quote(self.site_url, safe="")
        url = SEARCH_ANALYTICS_URL.format(site=encoded_site)
        rows: list[GscRow] = []
        start_row = 0
        while True:
            body: dict = {
                "dataState": self.data_state,
                "dimensions": list(dimensions),
                "endDate": end.isoformat(),
                "rowLimit": ROW_LIMIT,
                "startDate": start.isoformat(),
                "startRow": start_row,
            }
            if dimension_filters:
                body["dimensionFilterGroups"] = [
                    {"filters": dimension_filters, "groupType": "and"}
                ]
            response = self._request("POST", url, json_body=body)
            batch = response.json().get("rows") or []
            for raw in batch:
                keys = tuple(str(k) for k in (raw.get("keys") or []))
                rows.append(
                    GscRow(
                        clicks=float(raw.get("clicks") or 0),
                        ctr=float(raw.get("ctr") or 0),
                        impressions=float(raw.get("impressions") or 0),
                        keys=keys,
                        position=float(raw.get("position") or 0),
                    )
                )
            if len(batch) < ROW_LIMIT:
                break
            start_row += ROW_LIMIT
        return rows

    def available_dates(self, start: date, end: date) -> list[date]:
        rows = self.query(start, end, ("date",))
        out: list[date] = []
        for row in rows:
            if not row.keys:
                continue
            out.append(date.fromisoformat(row.keys[0]))
        return sorted(out)
