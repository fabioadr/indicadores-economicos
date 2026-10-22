from __future__ import annotations

from pipeline.gsc.urls import (
    canonical_path,
    is_asset_path,
    is_index_html,
    is_published_path,
    is_www,
)


def test_canonical_apex_indicator():
    assert (
        canonical_path("https://indicadoreseconomicoshoje.com.br/cdi/")
        == "/cdi/"
    )


def test_canonical_strips_index_html():
    assert (
        canonical_path(
            "https://www.indicadoreseconomicoshoje.com.br/inpc/index.html"
        )
        == "/inpc/"
    )


def test_canonical_keeps_png():
    url = (
        "https://www.indicadoreseconomicoshoje.com.br/inpc/"
        "grafico-variacao-rentabilidade-inpc-2021.png"
    )
    assert canonical_path(url).endswith(".png")
    assert is_asset_path(url)


def test_www_and_index_flags():
    www = "https://www.indicadoreseconomicoshoje.com.br/tr/index.html"
    apex = "https://indicadoreseconomicoshoje.com.br/tr/"
    assert is_www(www)
    assert not is_www(apex)
    assert is_index_html(www)
    assert not is_index_html(apex)


def test_published_path_matches_slug_and_static():
    slugs = {"cdi", "ipca"}
    assert is_published_path("/cdi/", slugs)
    assert is_published_path("/", slugs)
    assert is_published_path("/inflacao/", slugs)
    assert is_published_path("/comparar/juros-vs-inflacao/", slugs)
    assert not is_published_path("/pib/", slugs)
    assert not is_published_path("/cdi/grafico.png", slugs)
