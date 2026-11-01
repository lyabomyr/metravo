from __future__ import annotations

from ..listings.models import ListingEvent
from ..scanning.notifier import ListingNotifier
from ..searches.models import Search
from ..users.models import User
from .client import TelegramClient
from .formatter import ListingMessageFormatter
from .link_service import TelegramLinkService


class TelegramNotifier(ListingNotifier):
    def __init__(self, client: TelegramClient, links: TelegramLinkService, formatter: ListingMessageFormatter):
        self._client = client
        self._links = links
        self._formatter = formatter

    def notify(self, user: User, search: Search, events: list[ListingEvent]) -> int:
        sent = 0
        for chat in self._links.active_chats_of(user):
            for text in self._formatter.messages(search, events):
                sent += int(self._client.send_message(chat.chat_id, text))
        return sent
