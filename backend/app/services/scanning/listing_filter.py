from __future__ import annotations

import re

from ..connectors.models import Listing
from ..searches.models import Search

#: Titles that offer something other than a home. A flat search on Otodom also
#: returns "GARAŻ - 17m2"; "62 m² + garaż" is still a flat, so only the start counts.
_NOT_A_HOME = re.compile(
    r"^\W*(garaż|garaz|miejsce (postojowe|parkingowe)|komórka lokatorska"
    r"|lokal (użytkowy|uzytkowy|usługowy|uslugowy|biurowy|handlowy|komercyjny))",
    re.IGNORECASE,
)
#: Other spellings the portals use for a word a search rejects.
SPELLINGS: dict[str, tuple[str, ...]] = {"suterena": ("suteryna",)}


class ListingFilter:
    """Decides whether a listing fits a search.

    A value the portal did not publish never rejects on its own — bailiff
    auctions rarely state the area, and they are worth seeing. Two
    exception: an unpriced listing cannot be checked against a price limit.
    A required keyword rejects only a listing whose description we have —
    most results pages show just a title, and "balkon" is rarely in it. A
    limit left empty (None) does not filter at all.
    """

    def __init__(self, search: Search):
        self._search = search
        self._reject = [(word, _prefix_pattern(word, *SPELLINGS.get(word.lower(), ()))) for word in search.reject_keywords]
        self._required = [(word, _prefix_pattern(word)) for word in search.required_keywords]

    def reason_to_reject(self, listing: Listing) -> str | None:
        search = self._search
        priced = search.max_price is not None or search.min_price is not None or search.max_price_per_m2
        if listing.price is None and priced:
            return "no price published"
        if listing.price is not None and search.max_price is not None and listing.price > search.max_price:
            return f"price {listing.price} > {search.max_price}"
        if listing.price is not None and search.min_price is not None and listing.price < search.min_price:
            return f"price {listing.price} < {search.min_price}"
        if listing.area is not None and search.min_area is not None and listing.area < search.min_area:
            return f"area {listing.area} < {search.min_area}"
        if search.max_area is not None and listing.area is not None and listing.area > search.max_area:
            return f"area {listing.area} > {search.max_area}"
        if search.min_rooms and listing.rooms is not None and listing.rooms < search.min_rooms:
            return f"rooms {listing.rooms} < {search.min_rooms}"
        if search.max_rooms and listing.rooms is not None and listing.rooms > search.max_rooms:
            return f"rooms {listing.rooms} > {search.max_rooms}"
        if search.max_price_per_m2 and listing.area and listing.price is not None:
            per_m2 = listing.price / listing.area
            if per_m2 > search.max_price_per_m2:
                return f"{per_m2:.0f} zł/m² > {search.max_price_per_m2}"
        if search.min_build_year and listing.build_year and listing.build_year < search.min_build_year:
            return f"built {listing.build_year} < {search.min_build_year}"
        if match := _NOT_A_HOME.match(listing.title or ""):
            return f"not a home: {match.group(1).lower()}"
        text = " ".join(filter(None, (listing.title, listing.description, listing.location)))
        for word, pattern in self._reject:
            if pattern.search(text):
                return f"keyword {word}"
        if listing.description:  # without one, a missing word proves nothing
            for word, pattern in self._required:
                if not pattern.search(text):
                    return f"missing required keyword {word}"
        return None

    def accepts(self, listing: Listing) -> bool:
        return self.reason_to_reject(listing) is None


def _prefix_pattern(*spellings: str) -> re.Pattern:
    """Match at a word start: Polish inflection appends endings ("udział" → "udziału")."""
    return re.compile(rf"(?<!\w)(?:{'|'.join(map(re.escape, spellings))})", re.IGNORECASE)


def reason_code(reason: str) -> str:
    """A rejection, as the search card names it: a limit, or the word that decided."""
    if reason.startswith("keyword "):
        return "reject:" + reason.removeprefix("keyword ")
    if reason.startswith("missing required keyword "):
        return "missing:" + reason.removeprefix("missing required keyword ")
    if "zł/m²" in reason:
        return "per_m2"
    first = reason.split(" ", 1)[0]
    return {"no": "price", "price": "price", "area": "area", "rooms": "rooms", "built": "year"}.get(first, "other")
