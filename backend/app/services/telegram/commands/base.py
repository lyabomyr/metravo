from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...users.models import User


@dataclass(frozen=True)
class CommandContext:
    chat_id: str
    chat_title: str
    argument: str
    user: User | None  # None until the chat is linked to an account


class BaseCommand(ABC):
    """One Telegram command. Add a subclass and register it in ``dispatcher.py``."""

    name: str
    description: str
    #: Most commands only make sense for a chat that belongs to an account.
    requires_account: bool = True

    @abstractmethod
    def run(self, context: CommandContext) -> str:
        """Return the reply (HTML). Raise ``AppError`` to reply with its message."""
