from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramChat:
    chat_id: str
    user_id: str
    title: str
    paused: bool
    linked_at: str
    #: False: the chat hears every search. True: only the searches routed to it.
    only_selected: bool = False


@dataclass(frozen=True)
class LinkToken:
    token: str
    user_id: str
    expires_at: str
    used_at: str | None
    #: Made from a search's page: the chat it connects hears that search only.
    search_id: str | None = None


@dataclass(frozen=True)
class TelegramLink:
    """Deep links that finish the setup with one tap in Telegram."""

    token: str
    private_url: str
    group_url: str
    expires_at: str
    #: Adds the bot to a channel as an admin that may post; the owner then posts ``channel_code`` there.
    channel_url: str = ""
    channel_code: str = ""
