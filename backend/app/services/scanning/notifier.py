from __future__ import annotations

from abc import ABC, abstractmethod

from ..listings.models import ListingEvent
from ..searches.models import Search
from ..users.models import User


class ListingNotifier(ABC):
    """Tells a user about new listings. Telegram implements it; tests fake it."""

    @abstractmethod
    def notify(self, user: User, search: Search, events: list[ListingEvent]) -> int:
        """Deliver the events; return how many messages went out."""


class SilentNotifier(ListingNotifier):
    def notify(self, user: User, search: Search, events: list[ListingEvent]) -> int:
        return 0
