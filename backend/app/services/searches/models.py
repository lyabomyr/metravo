from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ...core.clock import parse_iso
from ..connectors.models import DealType, PropertyType, SearchQuery

# Listings that are not a whole, normal flat. Prefix-matched, so "udział"
# also catches "udziału".
DEFAULT_REJECT_KEYWORDS: tuple[str, ...] = (
    "TBS", "T.B.S", "suterena", "półpiwnica", "polpiwnica", "poziom -1",
    "piwnica mieszkalna", "udział", "udzial", "współwłasnoś", "wspolwlasnos",
)


@dataclass
class Search:
    id: str
    name: str
    city: str
    max_price: int
    min_area: float
    deal_type: DealType = DealType.SALE
    property_type: PropertyType = PropertyType.FLAT
    min_price: int | None = None
    max_area: float | None = None
    min_rooms: int | None = None
    max_rooms: int | None = None
    max_price_per_m2: int | None = None
    min_build_year: int | None = None
    sources: list[str] = field(default_factory=list)
    #: Every one of these must appear (e.g. "balkon"). Empty = no requirement.
    required_keywords: list[str] = field(default_factory=list)
    reject_keywords: list[str] = field(default_factory=lambda: list(DEFAULT_REJECT_KEYWORDS))
    enabled: bool = True
    last_scanned_at: str | None = None
    created_at: str = ""

    @property
    def query(self) -> SearchQuery:
        return SearchQuery(
            city=self.city,
            deal_type=self.deal_type,
            property_type=self.property_type,
            max_price=self.max_price,
            min_area=self.min_area,
        )

    def is_due(self, now: datetime, interval_minutes: int) -> bool:
        if not self.enabled:
            return False
        last = parse_iso(self.last_scanned_at)
        return last is None or now - last >= timedelta(minutes=interval_minutes)
