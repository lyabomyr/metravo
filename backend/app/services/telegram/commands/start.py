from __future__ import annotations

from ....core.i18n import translator
from ...scanning.service import FIRST_DELIVERY
from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class StartCommand(BaseCommand):
    name = "start"
    requires_account = False

    def __init__(self, links: TelegramLinkService, website_url: str):
        self._links = links
        self._website = website_url

    def run(self, context: CommandContext) -> str:
        if not context.argument:
            if context.user:
                return context.t("tg.start.already", email=context.user.email)
            return context.t("tg.start.sign_in", url=self._website)
        user = self._links.consume(context.argument, context.chat_id, context.chat_title)
        connected = translator.t(user.locale, "tg.start.connected", email=user.email)
        return f"{connected}\n\n{translator.t(user.locale, 'tg.start.first_batch', n=FIRST_DELIVERY)}"
