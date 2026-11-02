from __future__ import annotations

import logging

from ..telegram.client import TelegramClient
from ..telegram.link_service import TelegramLinkService
from ..users.service import UserService

log = logging.getLogger(__name__)


class AdminAlerter:
    """Tells the admins (ADMIN_EMAILS) in their linked Telegram chats."""

    def __init__(self, users: UserService, links: TelegramLinkService, client: TelegramClient, admin_emails: frozenset[str]):
        self._users = users
        self._links = links
        self._client = client
        self._admin_emails = admin_emails

    def send(self, text: str) -> int:
        log.warning("ALERT %s", text)
        sent = 0
        for email in sorted(self._admin_emails):
            admin = self._users.by_email(email)
            if admin is None:
                continue
            for chat in self._links.chats_of(admin):
                sent += int(self._client.send_message(chat.chat_id, f"🚨 Metravo: {text}"))
        return sent
