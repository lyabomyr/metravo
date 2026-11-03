from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)

MAX_WAIT_SECONDS = 30


class TelegramClient(ABC):
    #: Called with (old id, new id) when a group turns out to have become a supergroup.
    on_chat_moved: Callable[[str, str], None] = staticmethod(lambda old, new: None)

    @abstractmethod
    def send_message(self, chat_id: str, text: str) -> bool:
        """Send HTML-formatted text. Return False instead of raising."""

    @abstractmethod
    def send_photo(self, chat_id: str, photo_url: str, caption: str) -> bool:
        """A photo by its address, with an HTML caption; Telegram downloads the picture itself."""

    @abstractmethod
    def set_webhook(self, url: str, secret: str) -> None:
        """Point Telegram at our webhook endpoint."""

    @abstractmethod
    def set_profile(self, profile: BotProfileText, language: str | None) -> bool:
        """The command menu and the "What can this bot do?" texts, for one language (None = default)."""


@dataclass(frozen=True)
class BotProfileText:
    commands: list[tuple[str, str]]
    description: str        # shown in an empty chat before Start, up to 512 characters
    short_description: str  # on the bot's profile and in shared links, up to 120


class HttpTelegramClient(TelegramClient):
    def __init__(self, bot_token: str, timeout: int = 15):
        self._base = f"https://api.telegram.org/bot{bot_token}"
        self._timeout = timeout

    def send_message(self, chat_id: str, text: str) -> bool:
        body = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        return self._send("sendMessage", body)

    def send_photo(self, chat_id: str, photo_url: str, caption: str) -> bool:
        if self._send("sendPhoto", {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}):
            return True
        # Telegram could not fetch or read the picture: the listing matters more than its photo.
        return self.send_message(chat_id, caption)

    def _send(self, method: str, body: dict) -> bool:
        for attempt in range(3):
            try:
                response = requests.post(f"{self._base}/{method}", json=body, timeout=self._timeout)
            except requests.RequestException as exc:
                log.warning("telegram %s failed: %s", method, exc)
                return False
            if response.status_code == 429 and attempt == 0:
                # Too many messages to one chat at once: Telegram says how long to wait.
                time.sleep(min(_retry_after(response), MAX_WAIT_SECONDS))
                continue
            if moved_to := _parameter(response, "migrate_to_chat_id"):
                # The group was upgraded to a supergroup; it now lives under a new id.
                self.on_chat_moved(str(body["chat_id"]), str(moved_to))
                body = {**body, "chat_id": str(moved_to)}
                continue
            if not response.ok:
                log.warning("telegram refused %s to %s: %s", method, body.get("chat_id"), response.text[:200])
            return response.ok
        return False

    def set_webhook(self, url: str, secret: str) -> None:
        response = requests.post(
            f"{self._base}/setWebhook",
            json={"url": url, "secret_token": secret, "allowed_updates": ["message", "channel_post", "my_chat_member"]},
            timeout=self._timeout,
        )
        response.raise_for_status()

    def set_profile(self, profile: BotProfileText, language: str | None) -> bool:
        scope = {"language_code": language} if language else {}
        calls = (
            ("setMyCommands", {"commands": [{"command": name, "description": text} for name, text in profile.commands]}),
            ("setMyDescription", {"description": profile.description}),
            ("setMyShortDescription", {"short_description": profile.short_description}),
        )
        ok = True
        for method, body in calls:
            try:
                response = requests.post(f"{self._base}/{method}", json={**body, **scope}, timeout=self._timeout)
                ok = ok and response.ok
                if not response.ok:
                    log.warning("telegram %s (%s) refused: %s", method, language or "default", response.text[:200])
            except requests.RequestException as exc:
                log.warning("telegram %s failed: %s", method, exc)
                ok = False
        return ok


def _parameter(response: requests.Response, name: str) -> int | None:
    """One of the ``parameters`` Telegram adds to an error (retry_after, migrate_to_chat_id)."""
    try:
        value = response.json().get("parameters", {}).get(name)
    except (ValueError, AttributeError):
        return None
    return int(value) if value is not None else None


def _retry_after(response: requests.Response) -> int:
    return _parameter(response, "retry_after") or 1


@dataclass(frozen=True)
class SentMessage:
    chat_id: str
    text: str
    photo: str | None = None


class RecordingTelegramClient(TelegramClient):
    """Keeps messages in memory. Used without a bot token: locally, in tests and e2e."""

    def __init__(self) -> None:
        self.outbox: list[SentMessage] = []
        self.profiles: dict[str | None, BotProfileText] = {}

    def send_message(self, chat_id: str, text: str) -> bool:
        self.outbox.append(SentMessage(chat_id, text))
        log.info("[telegram → %s] %s", chat_id, text[:120])
        return True

    def send_photo(self, chat_id: str, photo_url: str, caption: str) -> bool:
        self.outbox.append(SentMessage(chat_id, caption, photo_url))
        log.info("[telegram → %s] 🖼 %s", chat_id, caption[:120])
        return True

    def set_webhook(self, url: str, secret: str) -> None:
        log.info("webhook not set (no bot token): %s", url)

    def set_profile(self, profile: BotProfileText, language: str | None) -> bool:
        self.profiles[language] = profile
        return True
