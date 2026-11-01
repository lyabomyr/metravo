from __future__ import annotations

from ...core.service import BaseService
from ..connectors.registry import ConnectorRegistry
from ..listings.models import EventKind, ListingEvent
from ..listings.service import ListingService
from ..searches.models import Search
from ..searches.service import SearchService
from ..tenants.service import TenantService
from ..users.models import User
from ..users.service import UserService
from .fetch_cache import FetchCache
from .listing_filter import ListingFilter
from .models import ScanReport
from .notifier import ListingNotifier


class ScanService(BaseService):
    """One scan run across every user whose searches are due."""

    def __init__(
        self,
        tenants: TenantService,
        users: UserService,
        searches: SearchService,
        listings: ListingService,
        connectors: ConnectorRegistry,
        notifier: ListingNotifier,
    ):
        super().__init__()
        self._tenants = tenants
        self._users = users
        self._searches = searches
        self._listings = listings
        self._connectors = connectors
        self._notifier = notifier

    def run(self, only_user_id: str | None = None) -> ScanReport:
        report = ScanReport()
        cache = FetchCache()
        for tenant in self._tenants.all():
            if only_user_id and tenant.user_id != only_user_id:
                continue
            user = self._users.get(tenant.user_id)
            for search in self._searches.due(user):
                self._scan_search(user, search, cache, report)
        report.fetches = cache.fetches
        self.log.info("scan finished: %s", report)
        return report

    def _scan_search(self, user: User, search: Search, cache: FetchCache, report: ScanReport) -> None:
        plan = self._users.plan_of(user)
        listing_filter = ListingFilter(search)
        events: list[ListingEvent] = []
        for source in search.sources:
            connector = self._connectors.get(source)
            if connector is None or not plan.allows_source(source):
                continue
            result = cache.get(connector, connector.build_url(search.query))
            if result.error:
                report.errors.append(f"{source}: {result.error}")
            for listing in result.listings:
                report.listings_seen += 1
                if not listing_filter.accepts(listing):
                    continue
                event = self._listings.record(user.id, search.id, listing)
                if event is None:
                    continue
                if event.kind is EventKind.NEW:
                    report.new_listings += 1
                    events.append(event)
                else:
                    report.price_changes += 1
                    if plan.price_alerts:
                        events.append(event)
        self._searches.mark_scanned(user, search.id)
        report.searches_scanned += 1
        if events:
            report.messages_sent += self._notifier.notify(user, search, events)
