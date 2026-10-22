"""Erros do módulo GSC — falham loud, não são ConnectorError."""

from __future__ import annotations


class GscError(Exception):
    """Base do módulo Search Console."""


class GscConfigError(GscError):
    """GSC_SITE_URL / GSC_CREDENTIALS_PATH ausentes ou inválidos."""


class GscAuthError(GscError):
    """Falha ao obter token ou 403 (service account não está no GSC)."""


class GscFetchError(GscError):
    """Erro HTTP / rede ao chamar a Search Console API."""
