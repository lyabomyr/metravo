from __future__ import annotations

from ...core.clock import Clock
from ...core.database import Database
from ...core.service import BaseService
from ..connectors.cities import city_names
from ..connectors.models import Listing
from ..searches.models import Search
from ..users.models import User
from .models import EventKind, ListingEvent, PriceChange, StoredListing
from .repository import ListingRepository

MAX_PAGE_SIZE = 200


class ListingService(BaseService):
    def __init__(self, db: Database, clock: Clock):
        super().__init__()
        self._db = db
        self._clock = clock
        self._city_names = city_names()

    def latest(self, user: User, search_id: str | None = None, limit: int = 50) -> list[StoredListing]:
        return self._repo(user.id).latest(search_id, min(limit, MAX_PAGE_SIZE))

    def price_changes(self, user: User, limit: int = 50) -> list[PriceChange]:
        return self._repo(user.id).price_changes(min(limit, MAX_PAGE_SIZE))

    def record(self, user_id: str, search: Search, listing: Listing) -> ListingEvent | None:
        """Store a matched listing; return an event if the user should hear about it."""
        repo = self._repo(user_id)
        search_id = search.id
        now = self._clock.iso()
        stored = repo.get(search_id, listing.key)
        if stored is None:
            fuzzy = listing.fuzzy_key(self._city_names)
            if fuzzy and repo.has_twin(search_id, fuzzy, listing.source):
                return None  # same flat, already announced from another portal
            repo.insert(search_id, search.deal_type.value, listing, fuzzy, now)
            return ListingEvent(EventKind.NEW, listing)
        repo.touch(search_id, listing.key, listing.price, now)
        if stored.price is not None and listing.price is not None and stored.price != listing.price:
            repo.add_price_change(search_id, listing.key, stored.price, listing.price, now)
            return ListingEvent(EventKind.PRICE_CHANGE, listing, previous_price=stored.price)
        return None

    def _repo(self, user_id: str) -> ListingRepository:
        return ListingRepository(self._db, user_id)
