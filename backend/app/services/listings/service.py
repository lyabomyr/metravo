from __future__ import annotations

from ...core.clock import Clock
from ...core.database import Database
from ...core.service import BaseService
from ..connectors.models import Listing
from ..places.known import place_names
from ..searches.models import Search
from ..users.models import User
from .models import EventKind, ListingEvent, PriceChange, StoredListing
from .repository import ListingCatalog, ListingRepository

MAX_PAGE_SIZE = 200


class ListingService(BaseService):
    def __init__(self, db: Database, clock: Clock):
        super().__init__()
        self._db = db
        self._catalog = ListingCatalog(db)
        self._clock = clock
        self._city_names = place_names()

    def latest(self, user: User, search_id: str | None = None, limit: int = 50) -> list[StoredListing]:
        return self._repo(user.id).latest(search_id, min(limit, MAX_PAGE_SIZE))

    def price_changes(self, user: User, limit: int = 50) -> list[PriceChange]:
        return self._repo(user.id).price_changes(min(limit, MAX_PAGE_SIZE))

    def forget_search(self, user: User, search_id: str) -> None:
        """A deleted search takes its results with it; offers nobody else has go too."""
        self._repo(user.id).forget_search(search_id)
        self._catalog.drop_unmatched()

    def record(self, user_id: str, search: Search, listing: Listing) -> ListingEvent | None:
        """Store a matched listing; return an event if the user should hear about it."""
        repo = self._repo(user_id)
        now = self._clock.iso()
        fuzzy = listing.fuzzy_key(self._city_names)
        match = repo.match(search.id, listing.key)
        if match is None and fuzzy and repo.has_twin(search.id, fuzzy, listing.source):
            return None  # same flat, already announced from another portal
        self._remember(listing, search.deal_type.value, fuzzy, now)
        if match is None:
            repo.add(search.id, listing.key, listing.price, now)
            return ListingEvent(EventKind.NEW, listing)
        if match.price_seen is not None and listing.price is not None and match.price_seen != listing.price:
            repo.set_price_seen(search.id, listing.key, listing.price)
            return ListingEvent(EventKind.PRICE_CHANGE, listing, previous_price=match.price_seen)
        return None

    def _remember(self, listing: Listing, deal_type: str, fuzzy: str | None, now: str) -> None:
        """Keep the one shared copy of the offer current, writing only when something changed."""
        known = self._catalog.known(listing.key)
        if known is None:
            self._catalog.insert(listing, deal_type, fuzzy, now)
            return
        price, last_seen = known
        if price is not None and listing.price is not None and price != listing.price:
            self._catalog.add_price_change(listing.key, price, listing.price, now)
        if price != listing.price or last_seen[:10] != now[:10]:  # "last seen" is kept to the day
            self._catalog.seen(listing.key, listing.price, now)

    def _repo(self, user_id: str) -> ListingRepository:
        return ListingRepository(self._db, user_id)
