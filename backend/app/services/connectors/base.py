"""Base class every portal connector extends.

A connector only says *where* to look (``URL_TEMPLATE``) and *how to read a
page* (``parse``). Paging, de-duplication within a walk, polite delays and
error handling live here once.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from urllib.parse import quote

from .cities import get_city
from .fetchers import FetchError, PageFetcher
from .models import DealType, Listing, PropertyType, SearchQuery


@dataclass
class ConnectorResult:
    listings: list[Listing] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseConnector(ABC):
    name: str
    #: One ``str.format`` template per (deal, property) the portal can search.
    #: A missing combination means "this portal does not offer it".
    #: Placeholders: {city} {city_label} {region_slug} {region_name} {max_price} {min_area}
    URL_TEMPLATES: dict[tuple[DealType, PropertyType], str]

    def __init__(self, fetcher: PageFetcher, pages: int = 1, delay_seconds: float = 0.0):
        self.fetcher = fetcher
        self.pages = max(1, pages)
        self.delay_seconds = delay_seconds
        self.log = logging.getLogger(f"connectors.{self.name}")

    def supports(self, deal_type: DealType, property_type: PropertyType) -> bool:
        return (deal_type, property_type) in self.URL_TEMPLATES

    @property
    def capabilities(self) -> list[dict[str, str]]:
        return [{"deal_type": deal.value, "property_type": kind.value} for deal, kind in self.URL_TEMPLATES]

    def build_url(self, query: SearchQuery) -> str | None:
        """The results URL for this search, or ``None`` if the portal does not offer it."""
        template = self.URL_TEMPLATES.get((query.deal_type, query.property_type))
        if template is None:
            return None
        city = get_city(query.city)
        return template.format(
            city=city.key,
            city_label=quote(city.label),
            region_slug=city.region_slug,
            region_name=quote(city.region_name),
            max_price="" if query.max_price is None else int(query.max_price),
            min_area="" if query.min_area is None else f"{query.min_area:g}",
        )

    def scan(self, url: str) -> ConnectorResult:
        """Walk up to ``pages`` result pages. Never raises — one broken portal
        must not stop the others."""
        result = ConnectorResult()
        seen: set[str] = set()
        for page in range(1, self.pages + 1):
            try:
                html = self.fetcher.fetch(self.page_url(url, page))
            except FetchError as exc:
                if page > 1 and exc.status in (404, 410):
                    break  # walked past the last page
                result.error = str(exc)
                self.log.warning("fetch failed: %s", exc)
                break
            fresh = [listing for listing in self._safe_parse(html) if listing.external_id not in seen]
            if not fresh:
                break
            seen.update(listing.external_id for listing in fresh)
            result.listings.extend(fresh)
            if page < self.pages and self.delay_seconds:
                time.sleep(self.delay_seconds)
        return result

    def page_url(self, url: str, page: int) -> str:
        if page <= 1:
            return url
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}page={page}"

    @abstractmethod
    def parse(self, html: str) -> Iterable[Listing]:
        """Yield every listing on one result page. Skip, don't raise, on a bad card."""

    def _safe_parse(self, html: str) -> list[Listing]:
        try:
            return list(self.parse(html))
        except Exception:  # a portal layout change must not crash the scan
            self.log.exception("could not parse page")
            return []
