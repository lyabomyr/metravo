from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from ...core.clock import parse_iso
from ...core.i18n import translator
from ..connectors.models import DealType, Market, PropertyType, SearchQuery
from ..places.models import Place

#: How often a search may be scanned, in minutes. The plan sets the floor.
SCAN_INTERVALS: tuple[int, ...] = (5, 15, 30, 60, 180, 360, 720, 1440)
DEFAULT_SCAN_INTERVAL = 1440  # once a day


def describe_interval(minutes: int, locale: str = "en") -> str:
    """5 → "every 5 min", 60 → "hourly", 180 → "every 3 h", 1440 → "daily" — in the given language."""
    if minutes >= 1440:
        return translator.t(locale, "interval.daily")
    if minutes < 60:
        return translator.t(locale, "interval.minutes", n=minutes)
    if minutes == 60:
        return translator.t(locale, "interval.hourly")
    return translator.t(locale, "interval.hours", n=minutes // 60)


# Listings that are not a whole, normal flat. Prefix-matched, so "udział"
# also catches "udziału".
#: Places one search may cover: its own and up to four more.
MAX_PLACES = 5

DEFAULT_REJECT_KEYWORDS: tuple[str, ...] = (
    "TBS", "T.B.S", "suterena", "półpiwnica", "polpiwnica", "poziom -1",
    "piwnica mieszkalna", "udział", "udzial", "współwłasnoś", "wspolwlasnos",
    "z najemc",  # sold with a tenant inside: "z najemcą", "z najemcami"
)


@dataclass
class Search:
    id: str
    name: str
    place: Place
    #: None = no limit. A new search tracks everything until the user narrows it.
    max_price: int | None = None
    min_area: float | None = None
    deal_type: DealType = DealType.SALE
    property_type: PropertyType = PropertyType.FLAT
    min_price: int | None = None
    max_area: float | None = None
    min_rooms: int | None = None
    max_rooms: int | None = None
    max_price_per_m2: int | None = None
    min_build_year: int | None = None
    sources: list[str] = field(default_factory=list)
    #: Every one of these must appear (e.g. "balkon"). Empty = no requirement.
    required_keywords: list[str] = field(default_factory=list)
    reject_keywords: list[str] = field(default_factory=lambda: list(DEFAULT_REJECT_KEYWORDS))
    interval_minutes: int = DEFAULT_SCAN_INTERVAL
    #: Kilometres around ``place`` (see ``places.models.RADIUS_CHOICES``).
    radius_km: int = 0
    #: Other places searched the same way, with the same radius (``MAX_PLACES`` in all).
    more_places: list[Place] = field(default_factory=list)
    enabled: bool = True
    last_scanned_at: str | None = None
    created_at: str = ""
    #: The last scan: offers the portals showed, how many fit, and what turned most of the rest away.
    last_found: int | None = None
    last_fit: int | None = None
    last_reason: str | None = None
    #: None = new builds and second-hand alike (sales only).
    market: Market | None = None
    #: Offers from the owner only: portals that cannot tell are skipped.
    private_only: bool = False
    #: Floors, 0 = the ground floor; None = no limit (flats only).
    min_floor: int | None = None
    max_floor: int | None = None
    #: When the GitHub job last fetched this search's remote portals (``REMOTE_PORTALS``).
    remote_scanned_at: str | None = None

    @property
    def places(self) -> list[Place]:
        return [self.place, *self.more_places]

    @property
    def queries(self) -> list[SearchQuery]:
        """One per place: the portals search a single place (and its radius) at a time."""
        return [replace(self.query, place=place) for place in self.places]

    @property
    def query(self) -> SearchQuery:
        return SearchQuery(
            place=self.place,
            radius_km=self.radius_km,
            deal_type=self.deal_type,
            property_type=self.property_type,
            max_price=self.max_price,
            min_area=self.min_area,
            market=self.market,
            private_only=self.private_only,
            min_floor=self.min_floor,
            max_floor=self.max_floor,
        )

    def is_due(self, now: datetime, interval_minutes: int, remote: bool = False) -> bool:
        """``remote``: due for the GitHub job's portals, which keep their own clock."""
        if not self.enabled:
            return False
        last = parse_iso(self.remote_scanned_at if remote else self.last_scanned_at)
        return last is None or now - last >= timedelta(minutes=interval_minutes)
