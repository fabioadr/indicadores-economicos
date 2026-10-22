from __future__ import annotations

from datetime import date
from urllib.parse import quote

import httpx
import pytest
import respx

from pipeline.gsc.client import GscClient
from pipeline.gsc.exceptions import GscAuthError, GscFetchError

SITE = "sc-domain:indicadoreseconomicoshoje.com.br"
QUERY_URL = (
    "https://www.googleapis.com/webmasters/v3/sites/"
    f"{quote(SITE, safe='')}/searchAnalytics/query"
)
SITES_URL = "https://www.googleapis.com/webmasters/v3/sites"


@respx.mock
def test_query_paginates_and_maps_rows(monkeypatch):
    monkeypatch.setattr("pipeline.gsc.client.ROW_LIMIT", 2)
    first = {
        "rows": [
            {
                "clicks": 0,
                "ctr": 0,
                "impressions": 10,
                "keys": ["cdi hoje"],
                "position": 40,
            },
            {
                "clicks": 0,
                "ctr": 0,
                "impressions": 1,
                "keys": ["q1"],
                "position": 50,
            },
        ]
    }
    second = {
        "rows": [
            {
                "clicks": 1,
                "ctr": 0.2,
                "impressions": 5,
                "keys": ["ipca hoje"],
                "position": 12,
            }
        ]
    }
    route = respx.post(QUERY_URL).mock(
        side_effect=[
            httpx.Response(200, json=first),
            httpx.Response(200, json=second),
        ]
    )
    with GscClient(SITE, token="tok") as client:
        rows = client.query(date(2026, 9, 1), date(2026, 9, 1), ("query",))
    assert route.call_count == 2
    assert rows[0].keys == ("cdi hoje",)
    assert rows[-1].keys == ("ipca hoje",)
    assert rows[-1].clicks == 1


@respx.mock
def test_query_403_is_auth_error():
    respx.post(QUERY_URL).mock(return_value=httpx.Response(403, json={"error": "forbidden"}))
    with GscClient(SITE, token="tok") as client:
        with pytest.raises(GscAuthError, match="service account"):
            client.query(date(2026, 9, 1), date(2026, 9, 1), ("query",))


@respx.mock
def test_query_500_exhausted_raises_fetch_error(monkeypatch):
    monkeypatch.setattr("pipeline.gsc.client.time.sleep", lambda *_: None)
    respx.post(QUERY_URL).mock(return_value=httpx.Response(500, text="boom"))
    with GscClient(SITE, token="tok") as client:
        with pytest.raises(GscFetchError, match="500"):
            client.query(date(2026, 9, 1), date(2026, 9, 1), ("query",))


@respx.mock
def test_list_sites():
    respx.get(SITES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "siteEntry": [
                    {
                        "siteUrl": SITE,
                        "permissionLevel": "siteFullUser",
                    }
                ]
            },
        )
    )
    with GscClient(SITE, token="tok") as client:
        sites = client.list_sites()
    assert sites[0].site_url == SITE
    assert sites[0].permission_level == "siteFullUser"
