from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ....core.i18n import translator
from ...users.models import User


@dataclass(frozen=True)
class CommandContext:
    chat_id: str
    chat_title: str
    argument: str
    user: User | None  # None until the chat is linked to an account
    locale: str = "en"  # the account's language, or the Telegram app's until linked

    def t(self, key: str, /, **params) -> str:
        return translator.t(self.locale, key, **params)


class BaseCommand(ABC):
    """One Telegram command. Add a subclass and register it in ``dispatcher.py``."""

    name: str
    #: Most commands only make sense for a chat that belongs to an account.
    requires_account: bool = True

    def description(self, locale: str) -> str:
        return translator.t(locale, f"tg.cmd.{self.name}")

    @abstractmethod
    def run(self, context: CommandContext) -> str:
        """Return the reply (HTML). Raise ``AppError`` to reply with its message."""
