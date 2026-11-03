from __future__ import annotations

import threading
from collections import Counter

from ...core.errors import LimitReached
from ...core.service import BaseService
from ..connectors.models import SearchQuery
from ..connectors.registry import ConnectorRegistry
from ..listings.models import EventKind, ListingEvent
from ..listings.service import ListingService
from ..places.known import known_place
from ..searches.models import Search
from ..searches.service import SearchService
from ..users.models import User
from ..users.service import UserService
from .fetch_cache import FetchCache
from .listing_filter import ListingFilter, reason_code
from .models import ScanReport
from .notifier import ListingNotifier
from .portal_access import PortalAccess

#: How many already-found listings a newly connected channel receives per search
#: (the newest; the website tells the user to expect this one longer message).
FIRST_DELIVERY = 20


class ScanService(BaseService):
    """One scan run across every user whose searches are due."""

    def __init__(
        self,
        users: UserService,
        searches: SearchService,
        listings: ListingService,
        connectors: ConnectorRegistry,
        notifier: ListingNotifier,
        access: PortalAccess | None = None,
    ):
        super().__init__()
        self._users = users
        self._searches = searches
        self._listings = listings
        self._connectors = connectors
        self._notifier = notifier
        self._access = access
        # The scheduler and "Scan now" may fire together; one run at a time
        # keeps a listing from being recorded — and announced — twice.
        self._lock = threading.Lock()

    def run(self, only_user_id: str | None = None) -> ScanReport:
        with self._lock:
            return self._run(only_user_id)

    def check_portals(self) -> None:
        """One request per portal (flats for sale in Kraków), so the portals' state is known right after a start."""
        query = SearchQuery(place=known_place("krakow"))
        cache = FetchCache(self._access)
        for name in self._connectors.names:
            connector = self._connectors.get(name)
            if url := connector.build_url(query):
                cache.get(connector, url)
        self.log.info("portals: %s", {name: state["state"] for name, state in self._access.status().items()})

    def check_now(self, user: User) -> ScanReport:
        """"Check now" on the website: the user's due searches, if their plan is running."""
        if not self._users.is_active(user):
            raise LimitReached("plan.free_week_over")
        return self.run(only_user_id=user.id)

    def deliver_now(self, user: User) -> int:
        """A channel was just connected: start at once instead of waiting for the schedule.

        Listings found before the user connected were stored but announced to
        nobody, so they are sent now; a search never checked is scanned now.
        """
        if not self._users.is_active(user):
            return 0
        with self._lock:
            sent = 0
            cache, report = FetchCache(self._access), ScanReport()
            for search in self._searches.list(user):
                if not search.enabled:
                    continue
                if search.last_scanned_at is None:
                    self._scan_search(user, search, cache, report)
                    continue
                found = self._listings.latest(user, search.id, limit=FIRST_DELIVERY)
                if found:
                    events = [ListingEvent(EventKind.NEW, stored.as_listing()) for stored in found]
                    sent += self._notifier.notify(user, search, events)
            return sent + report.messages_sent

    def _run(self, only_user_id: str | None) -> ScanReport:
        report = ScanReport()
        cache = FetchCache(self._access)
        for user_id in self._searches.owners():
            if only_user_id and user_id != only_user_id:
                continue
            user = self._users.get(user_id)
            if not user.active:
                continue  # the free week is over: nothing is checked or sent
            for search in self._searches.due(user):
                self._scan_search(user, search, cache, report)
        report.fetches = cache.fetches
        if report.searches_scanned:
            self.log.info("scan finished: %s", report)
        return report

    def _scan_search(self, user: User, search: Search, cache: FetchCache, report: ScanReport) -> None:
        plan = self._users.plan_of(user)
        listing_filter = ListingFilter(search)
        events: list[ListingEvent] = []
        found, fit, reasons = 0, 0, Counter()
        for source in search.sources:
            connector = self._connectors.get(source)
            if connector is None or not plan.allows_source(source):
                continue
            url = connector.build_url(search.query)
            if url is None:
                continue  # this portal does not offer e.g. rentals
            result = cache.get(connector, url)
            if result.error:
                report.errors.append(f"{source}: {result.error}")
            for listing in result.listings:
                report.listings_seen += 1
                found += 1
                if reason := listing_filter.reason_to_reject(listing):
                    reasons[reason_code(reason)] += 1
                    continue
                fit += 1
                event = self._listings.record(user.id, search, listing)
                if event is None:
                    continue
                if event.kind is EventKind.NEW:
                    report.new_listings += 1
                    events.append(event)
                else:
                    report.price_changes += 1
                    if plan.price_alerts:
                        events.append(event)
        top_reason = reasons.most_common(1)[0][0] if reasons else None
        self._searches.mark_scanned(user, search.id, found, fit, top_reason)
        report.searches_scanned += 1
        if events:
            report.messages_sent += self._notifier.notify(user, search, events)
