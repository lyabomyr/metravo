from __future__ import annotations

from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class StartCommand(BaseCommand):
    name = "start"
    description = "connect this chat to your Metravo account"
    requires_account = False

    def __init__(self, links: TelegramLinkService, website_url: str):
        self._links = links
        self._website = website_url

    def run(self, context: CommandContext) -> str:
        if not context.argument:
            if context.user:
                return f"✅ This chat is connected to <b>{context.user.email}</b>. /help lists what I can do."
            return f'👋 Sign in at <a href="{self._website}">Metravo</a> and press “Connect Telegram” — it takes two clicks.'
        user = self._links.consume(context.argument, context.chat_id, context.chat_title)
        return (
            f"✅ Connected to <b>{user.email}</b>.\n"
            "New flats matching your searches will arrive here. /help lists the commands."
        )
