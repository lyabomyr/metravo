from __future__ import annotations

from ..connectors.base import BaseConnector, ConnectorResult
from .portal_access import PortalAccess


class FetchCache:
    """One fetch per (portal, URL) per scan run.

    Many users watch the same city with similar budgets. Fetching each page
    once and filtering per search keeps the load on the portals flat as the
    number of users grows — the difference between "a scanner" and "a bot
    that gets banned".
    """

    def __init__(self, access: PortalAccess | None = None) -> None:
        self._results: dict[tuple[str, str], ConnectorResult] = {}
        self._access = access

    def get(self, connector: BaseConnector, url: str) -> ConnectorResult:
        key = (connector.name, url)
        if key not in self._results:
            self._results[key] = self._fetch(connector, url)
        return self._results[key]

    def _fetch(self, connector: BaseConnector, url: str) -> ConnectorResult:
        if self._access is None:
            return connector.scan(url)
        if not self._access.allows(connector.name):
            until = self._access.paused_until(connector.name)
            return ConnectorResult(error=f"paused: the portal refused us; next try {until:%H:%M} UTC")
        result = connector.scan(url)
        self._access.record(connector.name, result)
        return result

    @property
    def fetches(self) -> int:
        return len(self._results)
