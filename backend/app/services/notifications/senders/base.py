from __future__ import annotations

from abc import ABC, abstractmethod

from ...listings.models import ListingEvent
from ...searches.models import Search
from ...users.models import User


class ChannelSender(ABC):
    """Delivers listings over one channel. One subclass per channel in ``channels.py``."""

    channel: str

    @abstractmethod
    def deliver(self, user: User, address: str, search: Search, events: list[ListingEvent]) -> int:
        """Send the events to ``address`` (unused where the channel knows the user); return messages sent."""

    @abstractmethod
    def send_test(self, user: User, address: str) -> bool:
        """A short message that proves the channel reaches the user. False if it could not be sent."""
