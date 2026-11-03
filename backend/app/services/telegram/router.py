from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, status

from ...core.container import Container
from ...core.errors import Forbidden
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .models import TelegramChat
from .schemas import LinkRequest, RouteChange, TelegramChatOut, TelegramLinkOut

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


def chat_out(chat: TelegramChat, receives: bool | None = None) -> TelegramChatOut:
    return TelegramChatOut(chat_id=chat.chat_id, title=chat.title, paused=chat.paused, linked_at=chat.linked_at,
                           only_selected=chat.only_selected, receives=receives)


@router.post("/link", response_model=TelegramLinkOut)
def create_link(body: LinkRequest | None = None, user: User = Depends(current_user),
                container: Container = Depends(get_container)):
    search_id = body.search_id if body else None
    if search_id:
        container.searches.get(user, search_id)  # someone else's search is "not found"
    link = container.telegram_links.create_link(user, search_id)
    return TelegramLinkOut(private_url=link.private_url, group_url=link.group_url, expires_at=link.expires_at,
                           channel_url=link.channel_url, channel_code=link.channel_code)


@router.get("/chats", response_model=list[TelegramChatOut])
def chats(user: User = Depends(current_user), container: Container = Depends(get_container)):
    return [chat_out(chat) for chat in container.telegram_links.chats_of(user)]


@router.get("/searches/{search_id}/chats", response_model=list[TelegramChatOut])
def search_chats(search_id: str, user: User = Depends(current_user), container: Container = Depends(get_container)):
    """Every chat of the user, and whether it gets this search."""
    container.searches.get(user, search_id)
    links = container.telegram_links
    return [chat_out(chat, links.hears(chat, search_id)) for chat in links.chats_of(user)]


@router.put("/chats/{chat_id}/searches/{search_id}", response_model=TelegramChatOut)
def route(chat_id: str, search_id: str, body: RouteChange, user: User = Depends(current_user),
          container: Container = Depends(get_container)):
    container.searches.get(user, search_id)
    all_ids = [search.id for search in container.searches.list(user)]
    chat = container.telegram_links.route(user, chat_id, search_id, body.receives, all_ids)
    return chat_out(chat, body.receives)


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink(chat_id: str, user: User = Depends(current_user), container: Container = Depends(get_container)):
    container.telegram_links.unlink(user, chat_id)


@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
    container: Container = Depends(get_container),
) -> dict:
    # Telegram echoes the secret we registered; anything else is not Telegram.
    if x_telegram_bot_api_secret_token != container.settings.telegram_webhook_secret:
        raise Forbidden("Bad webhook secret")
    container.telegram_dispatcher.handle(await request.json())
    return {"ok": True}
