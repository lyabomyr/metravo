from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, status

from ...core.container import Container
from ...core.errors import Forbidden
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import TelegramChatOut, TelegramLinkOut

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/link", response_model=TelegramLinkOut)
def create_link(user: User = Depends(current_user), container: Container = Depends(get_container)):
    link = container.telegram_links.create_link(user)
    return TelegramLinkOut(private_url=link.private_url, group_url=link.group_url, expires_at=link.expires_at)


@router.get("/chats", response_model=list[TelegramChatOut])
def chats(user: User = Depends(current_user), container: Container = Depends(get_container)):
    return [
        TelegramChatOut(chat_id=c.chat_id, title=c.title, paused=c.paused, linked_at=c.linked_at)
        for c in container.telegram_links.chats_of(user)
    ]


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
