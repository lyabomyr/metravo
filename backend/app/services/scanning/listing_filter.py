from __future__ import annotations

import re

from ..connectors.models import Listing
from ..searches.models import Search


class ListingFilter:
    """Decides whether a listing fits a search.

    A value the portal did not publish never rejects on its own — bailiff
    auctions rarely state the area, and they are worth seeing. Two
    exceptions: an unpriced listing cannot be checked against the budget, and
    a required keyword has to actually be there.
    """

    def __init__(self, search: Search):
        self._search = search
        self._reject = [_prefix_pattern(word) for word in search.reject_keywords]
        self._required = [_prefix_pattern(word) for word in search.required_keywords]

    def reason_to_reject(self, listing: Listing) -> str | None:
        search = self._search
        if listing.price is None:
            return "no price published"
        if listing.price > search.max_price:
            return f"price {listing.price} > {search.max_price}"
        if search.min_price is not None and listing.price < search.min_price:
            return f"price {listing.price} < {search.min_price}"
        if listing.area is not None and listing.area < search.min_area:
            return f"area {listing.area} < {search.min_area}"
        if search.max_area is not None and listing.area is not None and listing.area > search.max_area:
            return f"area {listing.area} > {search.max_area}"
        if search.min_rooms and listing.rooms is not None and listing.rooms < search.min_rooms:
            return f"rooms {listing.rooms} < {search.min_rooms}"
        if search.max_rooms and listing.rooms is not None and listing.rooms > search.max_rooms:
            return f"rooms {listing.rooms} > {search.max_rooms}"
        if search.max_price_per_m2 and listing.area:
            per_m2 = listing.price / listing.area
            if per_m2 > search.max_price_per_m2:
                return f"{per_m2:.0f} zł/m² > {search.max_price_per_m2}"
        if search.min_build_year and listing.build_year and listing.build_year < search.min_build_year:
            return f"built {listing.build_year} < {search.min_build_year}"
        text = " ".join(filter(None, (listing.title, listing.description, listing.location)))
        for pattern in self._reject:
            if pattern.search(text):
                return f"keyword {pattern.pattern}"
        for pattern in self._required:
            if not pattern.search(text):
                return f"missing required keyword {pattern.pattern}"
        return None

    def accepts(self, listing: Listing) -> bool:
        return self.reason_to_reject(listing) is None


def _prefix_pattern(word: str) -> re.Pattern:
    """Match at a word start: Polish inflection appends endings ("udział" → "udziału")."""
    return re.compile(rf"(?<!\w){re.escape(word)}", re.IGNORECASE)
