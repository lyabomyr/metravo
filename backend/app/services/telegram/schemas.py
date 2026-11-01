from __future__ import annotations

from pydantic import BaseModel


class TelegramLinkOut(BaseModel):
    private_url: str
    group_url: str
    expires_at: str


class TelegramChatOut(BaseModel):
    chat_id: str
    title: str
    paused: bool
    linked_at: str
