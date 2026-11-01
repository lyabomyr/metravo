from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramChat:
    chat_id: str
    user_id: str
    title: str
    paused: bool
    linked_at: str


@dataclass(frozen=True)
class LinkToken:
    token: str
    user_id: str
    expires_at: str
    used_at: str | None


@dataclass(frozen=True)
class TelegramLink:
    """Deep links that finish the setup with one tap in Telegram."""

    token: str
    private_url: str
    group_url: str
    expires_at: str
