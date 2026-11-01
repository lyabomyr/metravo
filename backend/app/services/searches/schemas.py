from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel, Field

from .models import DEFAULT_REJECT_KEYWORDS, Search


class SearchIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    city: str
    max_price: int = Field(gt=0)
    min_area: float = Field(gt=0)
    max_area: float | None = None
    min_build_year: int | None = None
    sources: list[str]
    reject_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_REJECT_KEYWORDS))
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
