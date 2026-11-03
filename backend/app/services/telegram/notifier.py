from __future__ import annotations

from ...core.i18n import translator
from ..listings.models import ListingEvent
from ..notifications.senders.base import ChannelSender
from ..searches.models import Search
from ..users.models import User
from .client import TelegramClient
from .formatter import ListingMessageFormatter
from .link_service import TelegramLinkService


class TelegramSender(ChannelSender):
    """Sends listings, each with its photo, to every Telegram chat the user linked and has not paused."""

    channel = "telegram"

    def __init__(self, client: TelegramClient, links: TelegramLinkService, formatter: ListingMessageFormatter):
        self._client = client
        self._links = links
        self._formatter = formatter

    def deliver(self, user: User, address: str, search: Search, events: list[ListingEvent]) -> int:
        sent = 0
        for chat in self._links.receivers(user, search.id):
            for card in self._formatter.cards(search, events, user.locale):
                if card.photo:
                    sent += int(self._client.send_photo(chat.chat_id, card.photo, card.text))
                else:
                    sent += int(self._client.send_message(chat.chat_id, card.text))
        return sent

    def send_test(self, user: User, address: str) -> bool:
        chats = self._links.active_chats_of(user)
        text = "✅ " + translator.t(user.locale, "channel.test_message")
        return bool(chats) and all([self._client.send_message(chat.chat_id, text) for chat in chats])
