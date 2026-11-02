from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)


class TelegramClient(ABC):
    @abstractmethod
    def send_message(self, chat_id: str, text: str) -> bool:
        """Send HTML-formatted text. Return False instead of raising."""

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
        try:
            response = requests.post(
                f"{self._base}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            log.warning("telegram send failed: %s", exc)
            return False
        if not response.ok:
            log.warning("telegram refused message to %s: %s", chat_id, response.text[:200])
        return response.ok

    def set_webhook(self, url: str, secret: str) -> None:
        response = requests.post(
            f"{self._base}/setWebhook",
            json={"url": url, "secret_token": secret, "allowed_updates": ["message", "my_chat_member"]},
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


@dataclass(frozen=True)
class SentMessage:
    chat_id: str
    text: str


class RecordingTelegramClient(TelegramClient):
    """Keeps messages in memory. Used without a bot token: locally, in tests and e2e."""

    def __init__(self) -> None:
        self.outbox: list[SentMessage] = []
        self.profiles: dict[str | None, BotProfileText] = {}

    def send_message(self, chat_id: str, text: str) -> bool:
        self.outbox.append(SentMessage(chat_id, text))
        log.info("[telegram → %s] %s", chat_id, text[:120])
        return True

    def set_webhook(self, url: str, secret: str) -> None:
        log.info("webhook not set (no bot token): %s", url)

    def set_profile(self, profile: BotProfileText, language: str | None) -> bool:
        self.profiles[language] = profile
        return True
