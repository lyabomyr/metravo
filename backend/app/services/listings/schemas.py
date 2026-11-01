from __future__ import annotations

from pydantic import BaseModel


class ListingOut(BaseModel):
    search_id: str
    key: str
    source: str
    url: str
    title: str
    price: int | None
    area: float | None
    rooms: int | None
    location: str | None
    image_url: str | None
    first_seen_at: str
    last_seen_at: str


class PriceChangeOut(BaseModel):
    search_id: str
    key: str
    title: str
    url: str
    old_price: int
    new_price: int
    changed_at: str
