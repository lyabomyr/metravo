from __future__ import annotations

from datetime import datetime, timedelta

from ...core.clock import Clock
from ...core.service import BaseService
from ..listings.service import ListingService
from ..telegram.link_service import TelegramLinkService

EVERY = timedelta(days=1)


class Housekeeping(BaseService):
    """Once a day, keeps the database small: offers gone from the portals and old link tokens go."""

    def __init__(self, listings: ListingService, telegram: TelegramLinkService, clock: Clock):
        super().__init__()
        self._listings = listings
        self._telegram = telegram
        self._clock = clock
        self._last: datetime | None = None

    def run_if_due(self) -> None:
        now = self._clock.now()
        if self._last and now - self._last < EVERY:
            return
        self._last = now
        offers, tokens = self._listings.forget_gone(), self._telegram.drop_old_tokens()
        if offers or tokens:
            self.log.info("housekeeping: %s gone offers, %s old link tokens removed", offers, tokens)
