from __future__ import annotations

from collections.abc import Iterable

from ...core.errors import Invalid
from ..listings.models import ListingEvent
from ..scanning.notifier import ListingNotifier
from ..searches.models import Search
from ..users.models import User
from .senders.base import ChannelSender
from .service import NotificationService


class FanOutNotifier(ListingNotifier):
    """Sends the same listings to every channel the user switched on.

    A channel without a sender yet (not live) is skipped silently; the user's
    choice is kept, so delivery starts the day its sender is added.
    """

    def __init__(self, settings: NotificationService, senders: Iterable[ChannelSender]):
        self._settings = settings
        self._senders = {sender.channel: sender for sender in senders}

    @property
    def live(self) -> frozenset[str]:
        return frozenset(self._senders)

    def send_test(self, user: User, code: str) -> None:
        """Prove a channel reaches the user, from the Alerts page."""
        setting = self._settings.setting(user, code)
        sender = self._senders.get(code)
        if sender is None or not setting.allowed or not setting.enabled:
            raise Invalid("channel.test_off", channel=setting.channel.name)
        if not sender.send_test(user, setting.address):
            raise Invalid("channel.test_failed", channel=setting.channel.name)

    def notify(self, user: User, search: Search, events: list[ListingEvent]) -> int:
        sent = 0
        for setting in self._settings.active(user):
            sender = self._senders.get(setting.channel.code)
            if sender:
                sent += sender.deliver(user, setting.address, search, events)
        return sent
