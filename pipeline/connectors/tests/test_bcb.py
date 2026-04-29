"""Tests for the BCB SGS connector. No real network calls — respx mocks httpx."""

from __future__ import annotations

from datetime import date

import httpx
import pytest
import respx

from pipeline.connectors.bcb import BCB_BASE_URL, BCBSGSConnector
from pipeline.connectors.base import FetchError, ParseError, get_connector


SERIES_ID = 433
URL = BCB_BASE_URL.format(series_id=SERIES_ID)


@pytest.fixture(autouse=True)
def _no_pagination_pause(monkeypatch):
    """Skip the 1s pause between paginated calls."""
    monkeypatch.setattr("pipeline.connectors.bcb.time.sleep", lambda _: None)


def test_registry_resolves_bcb_sgs():
    connector = get_connector("bcb_sgs")
    assert isinstance(connector, BCBSGSConnector)


@respx.mock
def test_single_window_parses_payload():
    payload = [
        {"data": "01/01/2024", "valor": "0.42"},
        {"data": "01/02/2024", "valor": "0.83"},
        {"data": "01/03/2024", "valor": "0.16"},
    ]
    route = respx.get(URL).mock(return_value=httpx.Response(200, json=payload))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2024, 1, 1),
        until=date(2024, 12, 31),
    )

    assert route.call_count == 1
    assert [p.reference_date for p in points] == [
        date(2024, 1, 1),
        date(2024, 2, 1),
        date(2024, 3, 1),
    ]
    assert [p.value for p in points] == [0.42, 0.83, 0.16]
    assert points[0].raw_value == "0.42"


@respx.mock
def test_pagination_concatenates_and_dedups_overlap():
    payload_w1 = [{"data": "01/01/2005", "valor": "0.30"}]
    payload_w2 = [
        {"data": "01/01/2015", "valor": "0.40"},
        {"data": "01/01/2015", "valor": "0.40"},  # duplicado dentro da mesma janela
    ]
    payload_w3 = [
        {"data": "01/01/2015", "valor": "0.40"},  # duplicado entre janelas
        {"data": "01/01/2024", "valor": "0.50"},
    ]
    responses = iter([
        httpx.Response(200, json=payload_w1),
        httpx.Response(200, json=payload_w2),
        httpx.Response(200, json=payload_w3),
    ])
    route = respx.get(URL).mock(side_effect=lambda request: next(responses))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2000, 1, 1),
        until=date(2024, 12, 31),
    )

    assert route.call_count == 3
    assert [p.reference_date for p in points] == [
        date(2005, 1, 1),
        date(2015, 1, 1),
        date(2024, 1, 1),
    ]
    assert [p.value for p in points] == [0.30, 0.40, 0.50]


@respx.mock
def test_http_error_raises_fetch_error():
    respx.get(URL).mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(FetchError):
        BCBSGSConnector().fetch(
            {"series_id": SERIES_ID},
            since=date(2024, 1, 1),
            until=date(2024, 12, 31),
        )


@respx.mock
def test_malformed_json_raises_parse_error():
    respx.get(URL).mock(
        return_value=httpx.Response(
            200,
            text="<html>504 Gateway Timeout</html>",
            headers={"content-type": "text/html"},
        )
    )

    with pytest.raises(ParseError):
        BCBSGSConnector().fetch(
            {"series_id": SERIES_ID},
            since=date(2024, 1, 1),
            until=date(2024, 12, 31),
        )


@respx.mock
def test_decimal_with_comma_is_parsed():
    payload = [{"data": "01/01/2024", "valor": "0,44"}]
    respx.get(URL).mock(return_value=httpx.Response(200, json=payload))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2024, 1, 1),
        until=date(2024, 1, 31),
    )

    assert points[0].value == 0.44
    assert points[0].raw_value == "0,44"
