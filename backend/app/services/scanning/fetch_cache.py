from __future__ import annotations

from ..connectors.base import BaseConnector, ConnectorResult


class FetchCache:
    """One fetch per (portal, URL) per scan run.

    Many users watch the same city with similar budgets. Fetching each page
    once and filtering per search keeps the load on the portals flat as the
    number of users grows — the difference between "a scanner" and "a bot
    that gets banned".
    """

    def __init__(self) -> None:
        self._results: dict[tuple[str, str], ConnectorResult] = {}

    def get(self, connector: BaseConnector, url: str) -> ConnectorResult:
        key = (connector.name, url)
        if key not in self._results:
            self._results[key] = connector.scan(url)
        return self._results[key]

    @property
    def fetches(self) -> int:
        return len(self._results)
