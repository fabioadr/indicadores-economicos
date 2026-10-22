"""Normalização de URLs do GSC para casar com slugs do catálogo."""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

SITE_HOSTS = frozenset(
    {
        "indicadoreseconomicoshoje.com.br",
        "www.indicadoreseconomicoshoje.com.br",
    }
)

STATIC_PATHS = frozenset(
    {
        "/",
        "/comparar/",
        "/calendario/",
        "/sobre/",
        "/contato/",
        "/politica-de-privacidade/",
    }
)

CATEGORY_PATHS = frozenset(
    {
        "/inflacao/",
        "/juros/",
        "/correcao-monetaria/",
        "/atividade/",
        "/construcao-civil/",
        "/poupanca/",
        "/mercado-imobiliario/",
        "/trabalho/",
    }
)

_ASSET_SUFFIXES = frozenset(
    {
        ".css",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".png",
        ".svg",
        ".webp",
    }
)


def canonical_path(page_url: str) -> str:
    """Apex path com barra final, sem `/index.html`. Assets conservam o arquivo."""
    parsed = urlparse(page_url)
    path = unquote(parsed.path or "/")
    if not path.startswith("/"):
        path = f"/{path}"
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    elif path.endswith("index.html"):
        path = path[: -len("index.html")]
        if not path.endswith("/"):
            path += "/"
    name = path.rsplit("/", 1)[-1]
    if "." in name:
        return path
    if not path.endswith("/"):
        path += "/"
    return path


def is_www(page_url: str) -> bool:
    host = (urlparse(page_url).hostname or "").lower()
    return host.startswith("www.")


def is_index_html(page_url: str) -> bool:
    path = unquote(urlparse(page_url).path or "")
    return path.endswith("index.html")


def is_asset_path(path_or_url: str) -> bool:
    path = canonical_path(path_or_url)
    suffix = PurePosixPath(path).suffix.lower()
    return suffix in _ASSET_SUFFIXES


def is_published_path(path: str, slugs: set[str]) -> bool:
    """True se o path é uma rota do site (indicador, categoria, estático)."""
    if is_asset_path(path):
        return False
    if path in STATIC_PATHS or path in CATEGORY_PATHS:
        return True
    if path.startswith("/comparar/"):
        return True
    stripped = path.strip("/")
    return stripped in slugs
