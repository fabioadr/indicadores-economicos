"""Base interfaces for data source connectors.

Every external source (BCB, IBGE, FGV, ...) implements `BaseConnector` and
registers itself with `@register("<name>")`. The pipeline core resolves a
connector by the `connector_type` stored on the `indicators` row.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class RawDataPoint:
    """Normalized point returned by any connector."""

    reference_date: date
    value: float
    raw_value: str


class ConnectorError(Exception):
    """Base error for connector failures."""


class FetchError(ConnectorError):
    """Error fetching data (network, HTTP status, timeout)."""


class ParseError(ConnectorError):
    """Error interpreting upstream payload (unexpected format)."""


class BaseConnector(ABC):
    """Interface every connector must implement."""

    @abstractmethod
    def fetch(
        self,
        config: dict[str, Any],
        since: date | None = None,
        until: date | None = None,
    ) -> list[RawDataPoint]:
        """Fetch data from the source.

        Returns a list ordered by `reference_date` ascending. `since`/`until`
        are inclusive; `None` means "from inception" / "until today".
        Raises `FetchError` or `ParseError` on failure.
        """


CONNECTORS: dict[str, type[BaseConnector]] = {}


def register(name: str) -> Callable[[type[BaseConnector]], type[BaseConnector]]:
    def decorator(cls: type[BaseConnector]) -> type[BaseConnector]:
        CONNECTORS[name] = cls
        return cls

    return decorator


def get_connector(name: str) -> BaseConnector:
    if name not in CONNECTORS:
        raise ValueError(f"Connector desconhecido: {name}")
    return CONNECTORS[name]()
