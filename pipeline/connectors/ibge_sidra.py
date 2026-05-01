"""IBGE SIDRA connector.

Fetches time series from the IBGE SIDRA API v3. Spec in
docs/fase-02/03-connectors.md.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
from dateutil.relativedelta import relativedelta

from .base import BaseConnector, FetchError, ParseError, RawDataPoint, register

SIDRA_BASE_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/"
    "{tabela}/periodos/{periodos}/variaveis/{variaveis}"
)
MAX_PERIODS_PER_REQUEST = 60
PAGINATION_PAUSE_SECONDS = 1.0
HTTP_TIMEOUT_SECONDS = 30.0
EARLIEST_DEFAULT_DATE = date(1990, 1, 1)
SIDRA_NULL_VALUES = ("-", "...", "", None)


@register("ibge_sidra")
class IBGESIDRAConnector(BaseConnector):
    """Connector for the IBGE SIDRA v3 API."""

    def fetch(
        self,
        config: dict[str, Any],
        since: date | None = None,
        until: date | None = None,
    ) -> list[RawDataPoint]:
        tabela = config["tabela"]
        variavel = config["variavel"]
        localidade = config.get("localidade", "N1[all]")
        classificacao = config.get("classificacao")
        target_nivel = self._extract_nivel_id(localidade)

        until = until or date.today().replace(day=1)
        since = since or EARLIEST_DEFAULT_DATE

        all_points: list[RawDataPoint] = []
        windows = list(self._period_windows(since, until))
        for i, window in enumerate(windows):
            all_points.extend(
                self._fetch_window(
                    tabela, variavel, window, localidade, classificacao, target_nivel
                )
            )
            if i < len(windows) - 1:
                time.sleep(PAGINATION_PAUSE_SECONDS)

        seen: set[date] = set()
        unique: list[RawDataPoint] = []
        for p in sorted(all_points, key=lambda x: x.reference_date):
            if p.reference_date not in seen:
                seen.add(p.reference_date)
                unique.append(p)
        return unique

    def _period_windows(self, since: date, until: date) -> Iterator[tuple[str, str]]:
        cursor = since.replace(day=1)
        until_first = until.replace(day=1)
        while cursor <= until_first:
            window_end = min(
                cursor + relativedelta(months=MAX_PERIODS_PER_REQUEST - 1),
                until_first,
            )
            yield cursor.strftime("%Y%m"), window_end.strftime("%Y%m")
            cursor = window_end + relativedelta(months=1)

    def _fetch_window(
        self,
        tabela: int,
        variavel: int,
        window: tuple[str, str],
        localidade: str,
        classificacao: str | None,
        target_nivel: str | None,
    ) -> list[RawDataPoint]:
        start, end = window
        periodos = f"{start}-{end}"
        url = SIDRA_BASE_URL.format(
            tabela=tabela, periodos=periodos, variaveis=variavel
        )
        params: dict[str, str] = {"localidades": localidade}
        if classificacao:
            params["classificacao"] = classificacao

        try:
            response = httpx.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise FetchError(
                f"Erro HTTP ao buscar SIDRA tabela={tabela} periodos={periodos}: {e}"
            ) from e

        try:
            data = response.json()
        except ValueError as e:
            raise ParseError(
                f"Resposta não-JSON do SIDRA tabela={tabela}: {e}"
            ) from e

        return list(self._parse_response(data, target_nivel))

    def _parse_response(
        self, data: Any, target_nivel: str | None
    ) -> Iterator[RawDataPoint]:
        if not isinstance(data, list) or not data:
            return

        for variavel_block in data:
            if not isinstance(variavel_block, dict):
                continue
            for resultado in variavel_block.get("resultados", []):
                for serie_block in resultado.get("series", []):
                    if target_nivel and not self._matches_nivel(
                        serie_block, target_nivel
                    ):
                        continue
                    serie = serie_block.get("serie", {}) or {}
                    for periodo_str, value_str in serie.items():
                        if value_str in SIDRA_NULL_VALUES:
                            continue
                        ref = self._parse_period(periodo_str)
                        try:
                            value = float(str(value_str).replace(",", "."))
                        except (TypeError, ValueError) as e:
                            raise ParseError(
                                f"Valor inválido no SIDRA: periodo={periodo_str}, "
                                f"valor={value_str!r} ({e})"
                            ) from e
                        yield RawDataPoint(
                            reference_date=ref,
                            value=value,
                            raw_value=str(value_str),
                        )

    def _matches_nivel(self, serie_block: dict[str, Any], target_nivel: str) -> bool:
        localidade = serie_block.get("localidade") or {}
        nivel = localidade.get("nivel") or {}
        return nivel.get("id") == target_nivel

    def _extract_nivel_id(self, localidade: str) -> str | None:
        """Derive the expected `localidade.nivel.id` from the config string.

        Examples: ``"N1[all]"`` → ``"N1"``, ``"N3[all]"`` → ``"N3"``,
        ``"BR"`` → ``"N1"`` (Brazil aggregate). Anything else (e.g. an explicit
        numeric locality id) returns ``None`` so all series pass through.
        """
        if not localidade:
            return None
        if localidade.upper() == "BR":
            return "N1"
        match = re.match(r"^(N\d+)", localidade)
        return match.group(1) if match else None

    def _parse_period(self, s: str) -> date:
        if len(s) != 6:
            raise ParseError(f"Período não-mensal não suportado pelo SIDRA: {s!r}")
        try:
            year = int(s[:4])
            month = int(s[4:])
            return date(year, month, 1)
        except ValueError as e:
            raise ParseError(f"Período inválido: {s!r} ({e})") from e
