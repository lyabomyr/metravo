from __future__ import annotations

from ...core.i18n import translator
from ...core.service import BaseService
from .client import BotProfileText, TelegramClient
from .commands.base import BaseCommand

#: Telegram shows the default texts to every language without its own.
DEFAULT_LANGUAGE = "en"


class BotProfile(BaseService):
    """What people see before and around a chat with the bot: the command menu, the
    "What can this bot do?" text and the profile line — in each language we speak.
    Published by the API at startup, so changing a text never needs BotFather."""

    def __init__(self, client: TelegramClient, commands: list[BaseCommand]):
        super().__init__()
        self._client = client
        self._commands = commands

    def publish(self) -> bool:
        ok = True
        for locale in translator.locales:
            language = None if locale == DEFAULT_LANGUAGE else locale
            ok = self._client.set_profile(self._text(locale), language) and ok
        self.log.info("bot profile published%s", "" if ok else " with errors")
        return ok

    def _text(self, locale: str) -> BotProfileText:
        return BotProfileText(
            commands=[(command.name, command.description(locale)) for command in self._commands],
            description=translator.t(locale, "tg.about.description"),
            short_description=translator.t(locale, "tg.about.short"),
        )
