"""Tests for the IBGE SIDRA connector. No real network calls — respx mocks httpx."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from pipeline.connectors.base import FetchError, ParseError, get_connector
from pipeline.connectors.ibge_sidra import (
    SIDRA_BASE_URL,
    IBGESIDRAConnector,
)


TABELA = 3065
VARIAVEL = 355

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "sidra"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / name).read_text())


def _url(periodos: str) -> str:
    return SIDRA_BASE_URL.format(tabela=TABELA, periodos=periodos, variaveis=VARIAVEL)


@pytest.fixture(autouse=True)
def _no_pagination_pause(monkeypatch):
    """Skip the 1s pause between paginated calls."""
    monkeypatch.setattr("pipeline.connectors.ibge_sidra.time.sleep", lambda _: None)


def test_registry_resolves_ibge_sidra():
    connector = get_connector("ibge_sidra")
    assert isinstance(connector, IBGESIDRAConnector)


@respx.mock
def test_single_window_parses_payload():
    payload = _load_fixture("ipca15_jan_mar_2024.json")
    route = respx.get(_url("202401-202403")).mock(
        return_value=httpx.Response(200, json=payload)
    )

    points = IBGESIDRAConnector().fetch(
        {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
        since=date(2024, 1, 1),
        until=date(2024, 3, 1),
    )

    assert route.call_count == 1
    assert [p.reference_date for p in points] == [
        date(2024, 1, 1),
        date(2024, 2, 1),
        date(2024, 3, 1),
    ]
    assert [p.value for p in points] == [0.31, 0.78, 0.36]
    assert points[0].raw_value == "0.31"


@respx.mock
def test_pagination_concatenates_and_dedups_overlap():
    """since spans 7+ years → at least 2 windows of 60 months each."""
    payload_w1 = [
        {
            "id": str(VARIAVEL),
            "variavel": "IPCA15 - Variação mensal",
            "unidade": "%",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {
                                "id": "1",
                                "nivel": {"id": "N1", "nome": "Brasil"},
                                "nome": "Brasil",
                            },
                            "serie": {"201801": "0.30", "201802": "0.40"},
                        }
                    ],
                }
            ],
        }
    ]
    payload_w2 = [
        {
            "id": str(VARIAVEL),
            "variavel": "IPCA15 - Variação mensal",
            "unidade": "%",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {
                                "id": "1",
                                "nivel": {"id": "N1", "nome": "Brasil"},
                                "nome": "Brasil",
                            },
                            # Overlap with w1 on 201802 — should dedup
                            "serie": {"201802": "0.40", "202312": "0.50"},
                        }
                    ],
                }
            ],
        }
    ]
    responses = iter(
        [
            httpx.Response(200, json=payload_w1),
            httpx.Response(200, json=payload_w2),
        ]
    )
    route = respx.get(url__startswith=SIDRA_BASE_URL.split("{")[0]).mock(
        side_effect=lambda request: next(responses)
    )

    points = IBGESIDRAConnector().fetch(
        {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
        since=date(2018, 1, 1),
        until=date(2023, 12, 1),
    )

    assert route.call_count == 2
    assert [p.reference_date for p in points] == [
        date(2018, 1, 1),
        date(2018, 2, 1),
        date(2023, 12, 1),
    ]
    assert [p.value for p in points] == [0.30, 0.40, 0.50]


@respx.mock
def test_dash_and_ellipsis_are_skipped():
    payload = _load_fixture("ipca15_with_dash.json")
    respx.get(_url("202401-202404")).mock(
        return_value=httpx.Response(200, json=payload)
    )

    points = IBGESIDRAConnector().fetch(
        {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
        since=date(2024, 1, 1),
        until=date(2024, 4, 1),
    )

    assert [p.reference_date for p in points] == [
        date(2024, 1, 1),
        date(2024, 3, 1),
    ]
    assert [p.value for p in points] == [0.31, 0.36]


@respx.mock
def test_http_404_raises_fetch_error():
    """SIDRA: 404 means table/variable does not exist — surface as error."""
    respx.get(_url("202401-202403")).mock(
        return_value=httpx.Response(404, text="Not Found")
    )

    with pytest.raises(FetchError):
        IBGESIDRAConnector().fetch(
            {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
        )


@respx.mock
def test_http_500_raises_fetch_error():
    respx.get(_url("202401-202403")).mock(
        return_value=httpx.Response(500, text="boom")
    )

    with pytest.raises(FetchError):
        IBGESIDRAConnector().fetch(
            {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
        )


@respx.mock
def test_malformed_json_raises_parse_error():
    respx.get(_url("202401-202403")).mock(
        return_value=httpx.Response(
            200,
            text="<html>504 Gateway Timeout</html>",
            headers={"content-type": "text/html"},
        )
    )

    with pytest.raises(ParseError):
        IBGESIDRAConnector().fetch(
            {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
        )


@respx.mock
def test_non_monthly_period_raises_parse_error():
    payload = [
        {
            "id": str(VARIAVEL),
            "variavel": "IPCA15 - Variação anual",
            "unidade": "%",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {
                                "id": "1",
                                "nivel": {"id": "N1", "nome": "Brasil"},
                                "nome": "Brasil",
                            },
                            "serie": {"2024": "4.50"},
                        }
                    ],
                }
            ],
        }
    ]
    respx.get(_url("202401-202403")).mock(
        return_value=httpx.Response(200, json=payload)
    )

    with pytest.raises(ParseError):
        IBGESIDRAConnector().fetch(
            {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
        )


@respx.mock
def test_multiple_localities_are_filtered_by_nivel():
    """Config asks for N1[all] but the response carries N1 + N3 series.

    Only the N1 series should be kept.
    """
    payload = [
        {
            "id": str(VARIAVEL),
            "variavel": "IPCA15 - Variação mensal",
            "unidade": "%",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {
                                "id": "1",
                                "nivel": {"id": "N1", "nome": "Brasil"},
                                "nome": "Brasil",
                            },
                            "serie": {"202401": "0.31", "202402": "0.78"},
                        },
                        {
                            "localidade": {
                                "id": "35",
                                "nivel": {"id": "N3", "nome": "Unidade da Federação"},
                                "nome": "São Paulo",
                            },
                            "serie": {"202401": "9.99", "202402": "9.99"},
                        },
                    ],
                }
            ],
        }
    ]
    respx.get(_url("202401-202402")).mock(
        return_value=httpx.Response(200, json=payload)
    )

    points = IBGESIDRAConnector().fetch(
        {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
        since=date(2024, 1, 1),
        until=date(2024, 2, 1),
    )

    assert [p.value for p in points] == [0.31, 0.78]


@respx.mock
def test_empty_response_returns_empty_list():
    """SIDRA quirk: HTTP 200 with [] for invalid params — treat as no data."""
    respx.get(_url("202401-202403")).mock(return_value=httpx.Response(200, json=[]))

    points = IBGESIDRAConnector().fetch(
        {"tabela": TABELA, "variavel": VARIAVEL, "localidade": "N1[all]"},
        since=date(2024, 1, 1),
        until=date(2024, 3, 1),
    )

    assert points == []
