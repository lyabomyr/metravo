from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from ...core.clock import Clock, new_id
from ...core.database import Database
from ...core.errors import Invalid, LimitReached, NotFound
from ...core.service import BaseService
from ..connectors.registry import ConnectorRegistry
from ..places.models import RADIUS_CHOICES
from ..users.models import User
from ..users.service import UserService
from .models import SCAN_INTERVALS, Search
from .repository import SearchRepository


class SearchService(BaseService):
    def __init__(
        self,
        db: Database,
        users: UserService,
        connectors: ConnectorRegistry,
        clock: Clock,
        on_delete: Callable[[User, str], None] = lambda user, search_id: None,
    ):
        super().__init__()
        self._db = db
        #: Drops what the search found; listings are another service's tables.
        self._on_delete = on_delete
        self._connectors = connectors
        self._users = users
        self._clock = clock

    def list(self, user: User) -> list[Search]:
        return self._repo(user.id).all()

    def get(self, user: User, search_id: str) -> Search:
        return self.require(self._repo(user.id).by_id(search_id), NotFound("search.not_found"))

    def create(self, user: User, draft: Search) -> Search:
        repo = self._repo(user.id)
        plan = self._users.plan_of(user)
        if repo.count() >= plan.max_searches:
            raise LimitReached("search.limit", plan=plan.name, n=plan.max_searches)
        search = replace(draft, id=new_id(), created_at=self._clock.iso(), last_scanned_at=None)
        self._validate(user, search)
        repo.save(search)
        return search

    def update(self, user: User, search_id: str, draft: Search) -> Search:
        current = self.get(user, search_id)
        # Changing what to look for means the next scan should run right away.
        search = replace(draft, id=current.id, created_at=current.created_at, last_scanned_at=None)
        self._validate(user, search)
        self._repo(user.id).save(search)
        return search

    def delete(self, user: User, search_id: str) -> None:
        if not self._repo(user.id).delete(search_id):
            raise NotFound("search.not_found")
        self._on_delete(user, search_id)

    def set_enabled_all(self, user: User, enabled: bool) -> None:
        self._repo(user.id).set_enabled_all(enabled)

    def due(self, user: User) -> list[Search]:
        """Searches whose own interval has elapsed since their last scan.

        The plan's floor still applies, so a search saved on Pro every 15 minutes
        drops back to the Free pace if the subscription ends.
        """
        floor = self._users.plan_of(user).min_interval_minutes
        now = self._clock.now()
        return [
            search for search in self._repo(user.id).all()
            if search.is_due(now, max(search.interval_minutes, floor))
        ]

    def owners(self) -> list[str]:
        return SearchRepository.owners(self._db)

    def mark_scanned(self, user: User, search_id: str) -> None:
        self._repo(user.id).mark_scanned(search_id, self._clock.iso())

    def _validate(self, user: User, search: Search) -> None:
        if not search.place.is_valid():
            raise Invalid("search.place_invalid")
        if search.radius_km not in RADIUS_CHOICES:
            raise Invalid("search.radius_invalid", choices=", ".join(map(str, RADIUS_CHOICES)))
        if (search.max_price is not None and search.max_price <= 0) or (search.min_area is not None and search.min_area <= 0):
            raise Invalid("search.budget_positive")
        if search.max_area is not None and search.min_area is not None and search.max_area < search.min_area:
            raise Invalid("search.area_range")
        if search.min_price is not None and search.max_price is not None and search.min_price > search.max_price:
            raise Invalid("search.price_range")
        if search.min_rooms and search.max_rooms and search.max_rooms < search.min_rooms:
            raise Invalid("search.rooms_range")
        if not search.sources:
            raise Invalid("search.no_portal")
        unsupported = [
            source for source in search.sources
            if (connector := self._connectors.get(source)) is None
            or not connector.supports(search.deal_type, search.property_type)
        ]
        if unsupported:
            raise Invalid(
                "search.portal_unsupported",
                sources=", ".join(unsupported), property=search.property_type.value, deal=search.deal_type.value,
            )
        if search.interval_minutes not in SCAN_INTERVALS:
            raise Invalid("search.interval_invalid", choices=", ".join(map(str, SCAN_INTERVALS)))
        plan = self._users.plan_of(user)
        if not plan.allows_interval(search.interval_minutes):
            raise LimitReached("search.interval_plan", plan=plan.name, minutes=plan.min_interval_minutes)
        locked = [source for source in search.sources if not plan.allows_source(source)]
        if locked:
            raise LimitReached("search.portal_plan", sources=", ".join(locked), plan=plan.name)

    def _repo(self, user_id: str) -> SearchRepository:
        return SearchRepository(self._db, user_id)
