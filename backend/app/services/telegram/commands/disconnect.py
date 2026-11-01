from __future__ import annotations

from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class DisconnectCommand(BaseCommand):
    name = "disconnect"
    description = "unlink this chat from your account"

    def __init__(self, links: TelegramLinkService):
        self._links = links

    def run(self, context: CommandContext) -> str:
        self._links.unlink_from_telegram(context.chat_id)
        return "👋 Disconnected. Connect again any time from the website."
