"""Tests for the BCB SGS connector. No real network calls — respx mocks httpx."""

from __future__ import annotations

from datetime import date

import httpx
import pytest
import respx

from pipeline.connectors.bcb import BCB_BASE_URL, MAX_FETCH_ATTEMPTS, BCBSGSConnector
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
    # 2000-01-01 → 2024-12-31 com janelas de 5 anos = 5 requests.
    payload_w1 = [{"data": "01/01/2005", "valor": "0.30"}]
    payload_w2 = []
    payload_w3 = [
        {"data": "01/01/2015", "valor": "0.40"},
        {"data": "01/01/2015", "valor": "0.40"},  # duplicado dentro da mesma janela
    ]
    payload_w4 = [
        {"data": "01/01/2015", "valor": "0.40"},  # duplicado entre janelas
    ]
    payload_w5 = [
        {"data": "01/01/2024", "valor": "0.50"},
    ]
    responses = iter([
        httpx.Response(200, json=payload_w1),
        httpx.Response(200, json=payload_w2),
        httpx.Response(200, json=payload_w3),
        httpx.Response(200, json=payload_w4),
        httpx.Response(200, json=payload_w5),
    ])
    route = respx.get(URL).mock(side_effect=lambda request: next(responses))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2000, 1, 1),
        until=date(2024, 12, 31),
    )

    assert route.call_count == 5
    assert [p.reference_date for p in points] == [
        date(2005, 1, 1),
        date(2015, 1, 1),
        date(2024, 1, 1),
    ]
    assert [p.value for p in points] == [0.30, 0.40, 0.50]


@respx.mock
def test_http_error_raises_fetch_error():
    route = respx.get(URL).mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(FetchError):
        BCBSGSConnector().fetch(
            {"series_id": SERIES_ID},
            since=date(2024, 1, 1),
            until=date(2024, 12, 31),
        )

    assert route.call_count == MAX_FETCH_ATTEMPTS


@respx.mock
def test_malformed_json_raises_parse_error():
    route = respx.get(URL).mock(
        return_value=httpx.Response(
            200,
            text="<html>504 Gateway Timeout</html>",
            headers={"content-type": "text/html"},
        )
    )

    with pytest.raises(ParseError, match="content-type="):
        BCBSGSConnector().fetch(
            {"series_id": SERIES_ID},
            since=date(2024, 1, 1),
            until=date(2024, 12, 31),
        )

    assert route.call_count == MAX_FETCH_ATTEMPTS


@respx.mock
def test_404_returns_empty_list():
    """BCB returns 404 when there is no data for the requested date range (e.g. future month)."""
    route = respx.get(URL).mock(return_value=httpx.Response(404, text="Not Found"))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2026, 4, 1),
        until=date(2026, 4, 30),
    )

    assert points == []
    assert route.call_count == 1


@respx.mock
def test_empty_body_is_retried_then_parsed():
    payload = [{"data": "01/10/2026", "valor": "0.51"}]
    responses = iter([
        httpx.Response(200, text=""),
        httpx.Response(200, json=payload),
    ])
    route = respx.get(URL).mock(side_effect=lambda request: next(responses))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2026, 10, 1),
        until=date(2026, 10, 31),
    )

    assert route.call_count == 2
    assert points[0].value == 0.51


@respx.mock
def test_502_is_retried_then_parsed():
    payload = [{"data": "01/10/2026", "valor": "0.51"}]
    responses = iter([
        httpx.Response(502, text="<html>bad gateway</html>"),
        httpx.Response(200, json=payload),
    ])
    route = respx.get(URL).mock(side_effect=lambda request: next(responses))

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2026, 10, 1),
        until=date(2026, 10, 31),
    )

    assert route.call_count == 2
    assert points[0].value == 0.51


def test_connect_error_is_retried_then_parsed(monkeypatch):
    calls = {"n": 0}
    payload = [{"data": "01/10/2026", "valor": "0.51"}]

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("connection reset")
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_with_mock(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx._api, "Client", client_with_mock)

    points = BCBSGSConnector().fetch(
        {"series_id": SERIES_ID},
        since=date(2026, 10, 1),
        until=date(2026, 10, 31),
    )

    assert calls["n"] == 2
    assert points[0].value == 0.51


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
