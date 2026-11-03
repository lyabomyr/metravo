from __future__ import annotations

from pydantic import BaseModel


class TelegramLinkOut(BaseModel):
    private_url: str
    group_url: str
    expires_at: str
    channel_url: str = ""
    channel_code: str = ""


class TelegramChatOut(BaseModel):
    chat_id: str
    title: str
    paused: bool
    linked_at: str
    only_selected: bool = False
    #: On a search's page: does this chat get that search?
    receives: bool | None = None


class LinkRequest(BaseModel):
    search_id: str | None = None


class RouteChange(BaseModel):
    receives: bool
