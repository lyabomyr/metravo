from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..connectors.models import Listing


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
