from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel, Field

from ..connectors.models import DealType, PropertyType
from .models import DEFAULT_REJECT_KEYWORDS, DEFAULT_SCAN_INTERVAL, Search


class SearchIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    city: str
    deal_type: DealType = DealType.SALE
    property_type: PropertyType = PropertyType.FLAT
    min_price: int | None = Field(default=None, ge=0)
    max_price: int = Field(gt=0)
    min_area: float = Field(gt=0)
    max_area: float | None = None
    min_rooms: int | None = Field(default=None, ge=1)
    max_rooms: int | None = Field(default=None, ge=1)
    max_price_per_m2: int | None = Field(default=None, gt=0)
    min_build_year: int | None = None
    sources: list[str]
    required_keywords: list[str] = Field(default_factory=list)
    reject_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_REJECT_KEYWORDS))
    interval_minutes: int = DEFAULT_SCAN_INTERVAL
    enabled: bool = True

    def to_search(self) -> Search:
        return Search(id="", **self.model_dump())


class SearchOut(SearchIn):
    id: str
    last_scanned_at: str | None
    created_at: str

    @classmethod
    def of(cls, search: Search) -> SearchOut:
        return cls(**asdict(search))
