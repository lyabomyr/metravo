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


@dataclass(frozen=True)
class SentMessage:
    chat_id: str
    text: str


class RecordingTelegramClient(TelegramClient):
    """Keeps messages in memory. Used without a bot token: locally, in tests and e2e."""

    def __init__(self) -> None:
        self.outbox: list[SentMessage] = []

    def send_message(self, chat_id: str, text: str) -> bool:
        self.outbox.append(SentMessage(chat_id, text))
        log.info("[telegram → %s] %s", chat_id, text[:120])
        return True

    def set_webhook(self, url: str, secret: str) -> None:
        log.info("webhook not set (no bot token): %s", url)
