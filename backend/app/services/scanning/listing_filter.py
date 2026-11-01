from __future__ import annotations

import re

from ..connectors.models import Listing
from ..searches.models import Search


class ListingFilter:
    """Decides whether a listing fits a search.

    A value the portal did not publish never rejects on its own — bailiff
    auctions rarely state the area, and they are worth seeing. The one
    exception is price: an unpriced listing cannot be checked against the
    budget, so it is rejected.
    """

    def __init__(self, search: Search):
        self._search = search
        # Prefix match on a word start: Polish inflection appends endings
        # ("udział" → "udziału"), so a whole-word match would miss them.
        self._reject = [re.compile(rf"(?<!\w){re.escape(word)}", re.IGNORECASE) for word in search.reject_keywords]

    def reason_to_reject(self, listing: Listing) -> str | None:
        search = self._search
        if listing.price is None:
            return "no price published"
        if listing.price > search.max_price:
            return f"price {listing.price} > {search.max_price}"
        if listing.area is not None and listing.area < search.min_area:
            return f"area {listing.area} < {search.min_area}"
        if search.max_area is not None and listing.area is not None and listing.area > search.max_area:
            return f"area {listing.area} > {search.max_area}"
        if search.min_build_year and listing.build_year and listing.build_year < search.min_build_year:
            return f"built {listing.build_year} < {search.min_build_year}"
        text = " ".join(filter(None, (listing.title, listing.description, listing.location)))
        for pattern in self._reject:
            if pattern.search(text):
                return f"keyword {pattern.pattern}"
        return None

    def accepts(self, listing: Listing) -> bool:
        return self.reason_to_reject(listing) is None
