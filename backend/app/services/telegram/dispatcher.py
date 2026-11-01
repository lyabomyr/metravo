from __future__ import annotations

import logging

from ...core.errors import AppError
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
        reply = self._run(name, argument.strip(), chat_id, chat.get("title") or chat.get("username") or "")
        self._client.send_message(chat_id, reply)
        return reply

    def _run(self, name: str, argument: str, chat_id: str, chat_title: str) -> str:
        command = self._commands.get(name)
        if command is None:
            return "I don't know that command. /help lists what I can do."
        user = self._links.owner_of(chat_id)
        if command.requires_account and user is None:
            return f'This chat is not connected yet. Press “Connect Telegram” on <a href="{self._website}">the website</a>.'
        try:
            return command.run(CommandContext(chat_id=chat_id, chat_title=chat_title, argument=argument, user=user))
        except AppError as error:
            return f"⚠️ {error.message}"
        except Exception:
            log.exception("command /%s failed", name)
            return "⚠️ Something went wrong. Please try again."
