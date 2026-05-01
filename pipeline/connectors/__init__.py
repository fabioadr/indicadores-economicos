"""Connectors package — registry of data source adapters."""

from .base import (
    BaseConnector,
    ConnectorError,
    FetchError,
    ParseError,
    RawDataPoint,
    get_connector,
    register,
)
from . import bcb  # noqa: F401  — populates CONNECTORS registry
from . import ibge_sidra  # noqa: F401  — populates CONNECTORS registry

__all__ = [
    "BaseConnector",
    "ConnectorError",
    "FetchError",
    "ParseError",
    "RawDataPoint",
    "get_connector",
    "register",
]
