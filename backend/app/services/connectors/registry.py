"""All connectors in one place. Adding a portal = one class + one line here."""

from __future__ import annotations

from .base import BaseConnector
from .fetchers import PageFetcher
from .komornik.connector import KomornikConnector
from .morizon.connector import MorizonConnector
from .olx.connector import OlxConnector
from .otodom.connector import OtodomConnector

CONNECTOR_CLASSES: tuple[type[BaseConnector], ...] = (
    OtodomConnector,
    OlxConnector,
    MorizonConnector,
    KomornikConnector,
)


class ConnectorRegistry:
    def __init__(self, connectors: list[BaseConnector]):
        self._connectors = {connector.name: connector for connector in connectors}

    @classmethod
    def build(
        cls,
        default_fetcher: PageFetcher,
        overrides: dict[str, PageFetcher] | None = None,
        pages: int = 1,
        delay_seconds: float = 0.0,
    ) -> ConnectorRegistry:
        overrides = overrides or {}
        return cls([
            connector_class(overrides.get(connector_class.name, default_fetcher), pages, delay_seconds)
            for connector_class in CONNECTOR_CLASSES
        ])

    def get(self, name: str) -> BaseConnector | None:
        return self._connectors.get(name)

    @property
    def names(self) -> list[str]:
        return list(self._connectors)

    def capabilities(self) -> dict[str, list[dict[str, str]]]:
        """Which deal/property combinations each portal can search."""
        return {name: connector.capabilities for name, connector in self._connectors.items()}

    def filters(self) -> dict[str, list[str]]:
        """What else each portal can filter by ("market:primary", "private")."""
        return {name: sorted(connector.FILTERS) for name, connector in self._connectors.items()}
