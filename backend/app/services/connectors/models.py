from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..places.models import Place

# Location parts that say nothing about which flat it is.
_GENERIC_LOCATION_PARTS = frozenset({"polska", "poland"})


class DealType(str, Enum):
    SALE = "sale"
    RENT = "rent"


class PropertyType(str, Enum):
    FLAT = "flat"
    HOUSE = "house"


@dataclass(frozen=True)
class SearchQuery:
    """What a connector needs to build its search URL."""

    place: Place
    deal_type: DealType = DealType.SALE
    property_type: PropertyType = PropertyType.FLAT
    max_price: int | None = None
    min_area: float | None = None
    #: Kilometres around the place; 0 = the place itself.
    radius_km: int = 0


@dataclass
class Listing:
    """One offer (flat or house, sale or rent) from one portal. ``None`` means "not published"."""

    source: str
    external_id: str
    url: str
    title: str
    price: int | None = None
    area: float | None = None
    rooms: int | None = None
    location: str | None = None
    build_year: int | None = None
    description: str | None = None
    image_url: str | None = None

    @property
    def key(self) -> str:
        """Identity within one portal: ``"<source>:<id>"``."""
        return f"{self.source}:{self.external_id}"

    def fuzzy_key(self, city_names: frozenset[str] = frozenset()) -> str | None:
        """Probable identity across portals: price + rounded area + most specific place.

        ``None`` when there is not enough to tell flats apart; such listings
        are never merged.
        """
        if self.price is None or self.area is None or not self.location:
            return None
        ignored = _GENERIC_LOCATION_PARTS | city_names
        parts = [p.strip().lower() for p in self.location.split(",") if p.strip()]
        parts = [p for p in parts if p not in ignored]
        if not parts:
            return None
        return f"{self.price}|{round(self.area)}|{parts[0][:20]}"
