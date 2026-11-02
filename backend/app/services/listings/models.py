from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..connectors.models import Listing


@dataclass(frozen=True)
class Match:
    """A search matched an offer; ``price_seen`` is what the user was last told it costs."""

    price_seen: int | None


@dataclass(frozen=True)
class StoredListing:
    search_id: str
    key: str
    source: str
    deal_type: str
    url: str
    title: str
    price: int | None
    area: float | None
    rooms: int | None
    location: str | None
    image_url: str | None
    first_seen_at: str
    last_seen_at: str

    def as_listing(self) -> Listing:
        source, _, external_id = self.key.partition(":")
        return Listing(
            source=source, external_id=external_id, url=self.url, title=self.title, price=self.price,
            area=self.area, rooms=self.rooms, location=self.location, image_url=self.image_url,
        )


@dataclass(frozen=True)
class PriceChange:
    search_id: str
    key: str
    title: str
    url: str
    old_price: int
    new_price: int
    changed_at: str


class EventKind(str, Enum):
    NEW = "new"
    PRICE_CHANGE = "price_change"


@dataclass(frozen=True)
class ListingEvent:
    """Something worth telling the user about."""

    kind: EventKind
    listing: Listing
    previous_price: int | None = None
