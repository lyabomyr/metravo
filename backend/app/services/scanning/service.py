from __future__ import annotations

import threading
from collections import Counter

from ...core.errors import LimitReached
from ...core.service import BaseService
from ..connectors.models import Listing, SearchQuery
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
    """One scan run across every user whose searches are due.

    ``remote_portals`` are fetched by a GitHub Actions job instead of the API
    (Otodom answers GitHub's runners and refuses Render). ``run`` skips them,
    ``run_remote`` — the job — fetches only them, each on its own clock.
    """

    def __init__(
        self,
        users: UserService,
        searches: SearchService,
        listings: ListingService,
        connectors: ConnectorRegistry,
        notifier: ListingNotifier,
        access: PortalAccess | None = None,
        remote_portals: frozenset[str] = frozenset(),
    ):
        super().__init__()
        self._users = users
        self._searches = searches
        self._listings = listings
        self._connectors = connectors
        self._notifier = notifier
        self._access = access
        self._remote = remote_portals
        # The scheduler and "Scan now" may fire together; one run at a time
        # keeps a listing from being recorded — and announced — twice.
        self._lock = threading.Lock()

    def run(self, only_user_id: str | None = None) -> ScanReport:
        with self._lock:
            return self._run(only_user_id)

    def run_remote(self) -> ScanReport:
        """The GitHub job's run: only the remote portals, for searches due on the job's clock."""
        with self._lock:
            return self._run(None, remote=True)

    def check_portals(self) -> None:
        """One request per portal (flats for sale in Kraków), so the portals' state is known right after a start."""
        query = SearchQuery(place=known_place("krakow"))
        cache = FetchCache(self._access)
        for name in self._connectors.names:
            if name in self._remote:
                continue  # the GitHub job's business
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

    def _run(self, only_user_id: str | None, remote: bool = False) -> ScanReport:
        report = ScanReport()
        cache = FetchCache(self._access)
        for user_id in self._searches.owners():
            if only_user_id and user_id != only_user_id:
                continue
            user = self._users.get(user_id)
            if not user.active:
                continue  # the free week is over: nothing is checked or sent
            for search in self._searches.due(user, remote):
                self._scan_search(user, search, cache, report, remote)
        report.fetches = cache.fetches
        if report.searches_scanned:
            self.log.info("scan finished: %s", report)
        return report

    def ingest(self, user: User, search: Search, listings: list[Listing]) -> ScanReport:
        """Listings that arrived another way (a portal's alert email): same filter, store and alerts."""
        with self._lock:
            report = ScanReport()
            if not self._users.is_active(user) or not search.enabled:
                return report
            plan = self._users.plan_of(user)
            allowed = [listing for listing in listings if plan.allows_source(listing.source)]
            events = self._take(user, search, allowed, report, Counter())
            if events:
                report.messages_sent += self._notifier.notify(user, search, events)
            return report

    def _sources(self, user: User, search: Search) -> list[str]:
        """The search's portals that exist and that the user's plan allows."""
        plan = self._users.plan_of(user)
        return [source for source in search.sources if self._connectors.get(source) is not None and plan.allows_source(source)]

    def _scan_search(self, user: User, search: Search, cache: FetchCache, report: ScanReport, remote: bool = False) -> None:
        sources = self._sources(user, search)
        mine = [source for source in sources if (source in self._remote) == remote]
        if not mine and (remote or sources):
            return  # every portal of this search is fetched by the other side
        events: list[ListingEvent] = []
        reasons: Counter = Counter()
        seen_before, kept_before = report.listings_seen, report.new_listings + report.price_changes + report.kept
        for source in mine:
            connector = self._connectors.get(source)
            # One results page per place; an offer near two of them counts once.
            found_here: dict[str, Listing] = {}
            for query in search.queries:
                url = connector.build_url(query)
                if url is None:
                    break  # this portal does not offer e.g. rentals
                result = cache.get(connector, url)
                if result.error:
                    report.errors.append(f"{source}: {result.error}")
                for listing in result.listings:
                    found_here.setdefault(listing.key, listing)
            events += self._take(user, search, list(found_here.values()), report, reasons)
        found = report.listings_seen - seen_before
        fit = report.new_listings + report.price_changes + report.kept - kept_before
        top_reason = reasons.most_common(1)[0][0] if reasons else None
        if remote:
            self._searches.mark_remote_scanned(user, search.id)
        # "Last checked … found N, M fit" belongs to the API's run, unless the job is all there is.
        if not remote or len(mine) == len(sources):
            self._searches.mark_scanned(user, search.id, found, fit, top_reason)
        report.searches_scanned += 1
        if events:
            report.messages_sent += self._notifier.notify(user, search, events)

    def _take(self, user: User, search: Search, listings: list[Listing], report: ScanReport, reasons: Counter) -> list[ListingEvent]:
        """Filter and store listings for one search; the events worth telling the user about."""
        price_alerts = self._users.plan_of(user).price_alerts
        listing_filter = ListingFilter(search)
        events: list[ListingEvent] = []
        for listing in listings:
            report.listings_seen += 1
            if reason := listing_filter.reason_to_reject(listing):
                reasons[reason_code(reason)] += 1
                continue
            event = self._listings.record(user.id, search, listing)
            if event is None:
                report.kept += 1  # fits, and the user has already heard about it
            elif event.kind is EventKind.NEW:
                report.new_listings += 1
                events.append(event)
            else:
                report.price_changes += 1
                if price_alerts:
                    events.append(event)
        return events
