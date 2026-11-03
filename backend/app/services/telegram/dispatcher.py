from __future__ import annotations

import logging
from collections.abc import Callable

from ...core.errors import AppError
from ...core.i18n import translator
from ..users.models import User
from .client import TelegramClient
from .commands.base import BaseCommand, CommandContext
from .link_service import TelegramLinkService

log = logging.getLogger(__name__)


class CommandDispatcher:
    """Turns a Telegram update into a command call and sends the reply."""

    def __init__(
        self,
        commands: list[BaseCommand],
        links: TelegramLinkService,
        client: TelegramClient,
        website_url: str,
        on_connected: Callable[[User], None] = lambda user: None,
    ):
        self._commands = {command.name: command for command in commands}
        self._links = links
        self._client = client
        self._website = website_url
        self._on_connected = on_connected

    def handle(self, update: dict) -> str | None:
        """Process one update. Returns the reply text (handy for tests)."""
        if member := update.get("my_chat_member"):
            self._membership(member)
            return None
        message = update.get("message") or {}
        if moved_to := message.get("migrate_to_chat_id"):
            self._links.move_chat(str(message["chat"]["id"]), str(moved_to))
            return None
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        if not text.startswith("/") or "id" not in chat:
            return None
        chat_id = str(chat["id"])
        name, _, argument = text[1:].partition(" ")
        name = name.split("@")[0].lower()  # "/status@metravo_bot" in groups
        title = chat.get("title") or chat.get("username") or ""
        app_language = (message.get("from") or {}).get("language_code")
        was_linked = self._links.owner_of(chat_id) is not None
        reply = self._run(name, argument.strip(), chat_id, title, app_language)
        self._client.send_message(chat_id, reply)
        if not was_linked and (user := self._links.owner_of(chat_id)):
            self._on_connected(user)  # after the greeting, so it arrives first
        return reply

    def _membership(self, member: dict) -> None:
        """The bot was removed from a group, or blocked in a private chat: stop sending there."""
        if (member.get("new_chat_member") or {}).get("status") in ("left", "kicked"):
            self._links.unlink_from_telegram(str(member["chat"]["id"]))

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
