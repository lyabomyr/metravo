from __future__ import annotations

from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class ResumeCommand(BaseCommand):
    name = "resume"

    def __init__(self, links: TelegramLinkService):
        self._links = links

    def run(self, context: CommandContext) -> str:
        self._links.set_paused(context.chat_id, False)
        return context.t("tg.resume")
