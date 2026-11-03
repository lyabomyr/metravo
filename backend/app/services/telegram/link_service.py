from __future__ import annotations

import secrets
from datetime import timedelta

from ...core.clock import Clock, parse_iso
from ...core.errors import Invalid, NotFound
from ...core.service import BaseService
from ..users.models import User
from ..users.service import UserService
from .models import TelegramChat, TelegramLink
from .repository import TelegramRepository

LINK_TTL = timedelta(minutes=30)


class TelegramLinkService(BaseService):
    """The two-click setup.

    Click 1 (website): ``create_link`` returns ``t.me/<bot>?start=<token>``.
    Click 2 (Telegram): the user taps Start, the bot receives ``/start <token>``
    and ``consume`` binds that chat to the account.
    """

    def __init__(self, repo: TelegramRepository, users: UserService, bot_username: str, clock: Clock):
        super().__init__()
        self._repo = repo
        self._users = users
        self._bot = bot_username
        self._clock = clock

    def create_link(self, user: User, search_id: str | None = None) -> TelegramLink:
        """With ``search_id`` (the caller checked it is the user's), the chat it connects hears that search only."""
        # Telegram allows [A-Za-z0-9_-]{1,64} in a start parameter.
        token = secrets.token_urlsafe(24)
        expires_at = (self._clock.now() + LINK_TTL).isoformat(timespec="seconds")
        self._repo.add_token(token, user.id, expires_at, search_id)
        return TelegramLink(
            token=token,
            private_url=f"https://t.me/{self._bot}?start={token}",
            group_url=f"https://t.me/{self._bot}?startgroup={token}",
            channel_url=f"https://t.me/{self._bot}?startchannel&admin=post_messages",
            channel_code=f"/start {token}",
            expires_at=expires_at,
        )

    def consume(self, token: str, chat_id: str, title: str) -> User:
        link = self.require(self._repo.token(token), Invalid("telegram.link_invalid"))
        if link.used_at or parse_iso(link.expires_at) < self._clock.now():
            raise Invalid("telegram.link_expired")
        if not self._repo.use_token(token, self._clock.iso()):
            raise Invalid("telegram.link_used")
        existing = self._repo.chat(chat_id)
        if link.search_id is None:
            self._repo.link_chat(chat_id, link.user_id, title, self._clock.iso())
        elif existing and existing.user_id == link.user_id and not existing.only_selected:
            pass  # the chat already hears every search, this one included
        else:
            if not (existing and existing.user_id == link.user_id):
                self._repo.link_chat(chat_id, link.user_id, title, self._clock.iso(), only_selected=True)
            self._repo.add_route(chat_id, link.search_id, link.user_id)
        return self._users.get(link.user_id)

    def drop_old_tokens(self) -> int:
        """Links expire in half an hour; a day later nobody needs to hear "expired" instead of "invalid"."""
        return self._repo.drop_tokens_expired_before((self._clock.now() - timedelta(days=1)).isoformat(timespec="seconds"))

    def owner_of(self, chat_id: str) -> User | None:
        chat = self._repo.chat(chat_id)
        return self._users.get(chat.user_id) if chat else None

    def chat(self, chat_id: str) -> TelegramChat | None:
        return self._repo.chat(chat_id)

    def chats_of(self, user: User) -> list[TelegramChat]:
        return self._repo.chats_of(user.id)

    def active_chats_of(self, user: User) -> list[TelegramChat]:
        return [chat for chat in self.chats_of(user) if not chat.paused]

    def receivers(self, user: User, search_id: str) -> list[TelegramChat]:
        """The chats that get this search's listings now: not paused, and hearing every search or this one."""
        return [chat for chat in self.active_chats_of(user) if self.hears(chat, search_id)]

    def hears(self, chat: TelegramChat, search_id: str) -> bool:
        return not chat.only_selected or search_id in self._repo.routed_searches(chat.chat_id)

    def route(self, user: User, chat_id: str, search_id: str, on: bool, all_search_ids: list[str]) -> TelegramChat:
        """Send this search to this chat, or stop; ``all_search_ids`` are the user's searches."""
        chat = self._repo.chat(chat_id)
        if chat is None or chat.user_id != user.id:
            raise NotFound("telegram.chat_not_found")
        if on and chat.only_selected:
            self._repo.add_route(chat_id, search_id, user.id)
        elif not on and not chat.only_selected:
            # Hearing everything but this one: the rest become explicit choices.
            self._repo.set_only_selected(chat_id, True)
            for other in all_search_ids:
                if other != search_id:
                    self._repo.add_route(chat_id, other, user.id)
        elif not on:
            self._repo.drop_route(chat_id, search_id)
        return self._repo.chat(chat_id)

    def forget_search(self, user: User, search_id: str) -> None:
        self._repo.forget_search_routes(user.id, search_id)

    def set_paused(self, chat_id: str, paused: bool) -> None:
        self._repo.set_paused(chat_id, paused)

    def unlink(self, user: User, chat_id: str) -> None:
        chat = self._repo.chat(chat_id)
        if chat is None or chat.user_id != user.id:
            raise NotFound("telegram.chat_not_found")
        self._repo.unlink_chat(chat_id)

    def move_chat(self, old_id: str, new_id: str) -> None:
        """A group became a supergroup: Telegram gave it a new id, the link and pause stay."""
        if self._repo.move_chat(old_id, new_id):
            self.log.info("telegram chat %s is now %s", old_id, new_id)

    def unlink_from_telegram(self, chat_id: str) -> None:
        self._repo.unlink_chat(chat_id)

    def count_chats(self) -> int:
        return self._repo.count_chats()
