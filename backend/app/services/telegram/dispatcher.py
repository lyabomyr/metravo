from __future__ import annotations

import logging

from ...core.errors import AppError
from ...core.i18n import translator
from .client import TelegramClient
from .commands.base import BaseCommand, CommandContext
from .link_service import TelegramLinkService

log = logging.getLogger(__name__)


class CommandDispatcher:
    """Turns a Telegram update into a command call and sends the reply."""

    def __init__(self, commands: list[BaseCommand], links: TelegramLinkService, client: TelegramClient, website_url: str):
        self._commands = {command.name: command for command in commands}
        self._links = links
        self._client = client
        self._website = website_url

    def handle(self, update: dict) -> str | None:
        """Process one update. Returns the reply text (handy for tests)."""
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        if not text.startswith("/") or "id" not in chat:
            return None
        chat_id = str(chat["id"])
        name, _, argument = text[1:].partition(" ")
        name = name.split("@")[0].lower()  # "/status@metravo_bot" in groups
        title = chat.get("title") or chat.get("username") or ""
        app_language = (message.get("from") or {}).get("language_code")
        reply = self._run(name, argument.strip(), chat_id, title, app_language)
        self._client.send_message(chat_id, reply)
        return reply

    def _run(self, name: str, argument: str, chat_id: str, chat_title: str, app_language: str | None) -> str:
        user = self._links.owner_of(chat_id)
        locale = user.locale if user else translator.negotiate(app_language)
        command = self._commands.get(name)
        if command is None:
            return translator.t(locale, "tg.unknown")
        if command.requires_account and user is None:
            return translator.t(locale, "tg.not_connected", url=self._website)
        try:
            return command.run(CommandContext(chat_id=chat_id, chat_title=chat_title, argument=argument, user=user, locale=locale))
        except AppError as error:
            return f"⚠️ {error.text(locale)}"
        except Exception:
            log.exception("command /%s failed", name)
            return translator.t(locale, "tg.failed")
