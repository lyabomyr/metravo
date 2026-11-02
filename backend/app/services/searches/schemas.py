from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel, Field, model_validator

from ...core.errors import Invalid
from ..connectors.models import DealType, PropertyType
from ..places.known import known_place
from ..places.models import Place
from .models import DEFAULT_REJECT_KEYWORDS, DEFAULT_SCAN_INTERVAL, Search


class PlaceIO(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    path: str = Field(min_length=7, max_length=200)
    region_name: str = Field(min_length=1, max_length=60)
    lat: float
    lon: float
    detail: str = ""

    def to_place(self) -> Place:
        return Place(**self.model_dump())

    @classmethod
    def of(cls, place: Place) -> PlaceIO:
        return cls(**asdict(place))


class SearchFields(BaseModel):
    name: str = Field(min_length=1, max_length=80)
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
    radius_km: int = 0
    enabled: bool = True


class SearchIn(SearchFields):
    #: Any place picked on the website. ``city`` ("krakow") still works for a known city.
    place: PlaceIO | None = None
    city: str | None = None

    @model_validator(mode="after")
    def _has_a_place(self) -> SearchIn:
        if self.place is None and self.city is None:
            raise ValueError("place is required")
        return self

    def to_search(self) -> Search:
        place = self.place.to_place() if self.place else known_place(self.city or "")
        if place is None:
            raise Invalid("search.place_invalid")
        return Search(id="", place=place, **self.model_dump(exclude={"place", "city"}))


class SearchOut(SearchFields):
    id: str
    place: PlaceIO
    last_scanned_at: str | None
    created_at: str

    @classmethod
    def of(cls, search: Search) -> SearchOut:
        values = asdict(search)
        values["place"] = PlaceIO.of(search.place)
        return cls(**values)
