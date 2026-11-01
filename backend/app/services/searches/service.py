from __future__ import annotations

from dataclasses import replace

from ...core.clock import Clock, new_id
from ...core.errors import Invalid, LimitReached, NotFound
from ...core.service import BaseService
from ..connectors.cities import get_city
from ..tenants.service import TenantService
from ..users.models import User
from ..users.service import UserService
from .models import Search
from .repository import SearchRepository


class SearchService(BaseService):
    def __init__(self, tenants: TenantService, users: UserService, clock: Clock):
        super().__init__()
        self._tenants = tenants
        self._users = users
        self._clock = clock

    def list(self, user: User) -> list[Search]:
        return self._repo(user.id).all()

    def get(self, user: User, search_id: str) -> Search:
        return self.require(self._repo(user.id).by_id(search_id), NotFound("Search not found"))

    def create(self, user: User, draft: Search) -> Search:
        repo = self._repo(user.id)
        plan = self._users.plan_of(user)
        if repo.count() >= plan.max_searches:
            raise LimitReached(f"The {plan.name} plan allows {plan.max_searches} search(es)")
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
            raise NotFound("Search not found")

    def set_enabled_all(self, user: User, enabled: bool) -> None:
        self._repo(user.id).set_enabled_all(enabled)

    def due(self, user: User) -> list[Search]:
        """Searches whose plan interval has elapsed since their last scan."""
        interval = self._users.plan_of(user).scan_interval_minutes
        now = self._clock.now()
        return [search for search in self._repo(user.id).all() if search.is_due(now, interval)]

    def mark_scanned(self, user: User, search_id: str) -> None:
        self._repo(user.id).mark_scanned(search_id, self._clock.iso())

    def _validate(self, user: User, search: Search) -> None:
        get_city(search.city)
        if search.max_price <= 0 or search.min_area <= 0:
            raise Invalid("Budget and minimum area must be positive")
        if search.max_area is not None and search.max_area < search.min_area:
            raise Invalid("Maximum area is below minimum area")
        if not search.sources:
            raise Invalid("Pick at least one portal")
        plan = self._users.plan_of(user)
        locked = [source for source in search.sources if not plan.allows_source(source)]
        if locked:
            raise LimitReached(f"{', '.join(locked)} is not included in the {plan.name} plan")

    def _repo(self, user_id: str) -> SearchRepository:
        return SearchRepository(self._tenants.database_for(user_id))
