from __future__ import annotations

from ...core.database import Row
from ...core.repository import BaseRepository
from .models import LinkToken, TelegramChat


class TelegramRepository(BaseRepository):
    """Control database: which chat belongs to which user, and pending link tokens."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS telegram_chats (
            chat_id   TEXT PRIMARY KEY,
            user_id   TEXT NOT NULL,
            title     TEXT NOT NULL DEFAULT '',
            paused    INTEGER NOT NULL DEFAULT 0,
            linked_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS telegram_link_tokens (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at    TEXT
        )""",
    )

    # --- chats -----------------------------------------------------------

    def chat(self, chat_id: str) -> TelegramChat | None:
        return self._to_chat(self._one("SELECT * FROM telegram_chats WHERE chat_id = ?", (chat_id,)))

    def chats_of(self, user_id: str) -> list[TelegramChat]:
        rows = self._all("SELECT * FROM telegram_chats WHERE user_id = ? ORDER BY linked_at", (user_id,))
        return [self._to_chat(row) for row in rows]

    def link_chat(self, chat_id: str, user_id: str, title: str, now: str) -> None:
        self._exec(
            "INSERT OR REPLACE INTO telegram_chats (chat_id, user_id, title, paused, linked_at) VALUES (?, ?, ?, 0, ?)",
            (chat_id, user_id, title, now),
        )

    def unlink_chat(self, chat_id: str) -> int:
        return self._exec("DELETE FROM telegram_chats WHERE chat_id = ?", (chat_id,))

    def set_paused(self, chat_id: str, paused: bool) -> None:
        self._exec("UPDATE telegram_chats SET paused = ? WHERE chat_id = ?", (int(paused), chat_id))

    def count_chats(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM telegram_chats")["n"]

    # --- link tokens -----------------------------------------------------

    def add_token(self, token: str, user_id: str, expires_at: str) -> None:
        self._exec(
            "INSERT INTO telegram_link_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )

    def token(self, token: str) -> LinkToken | None:
        row = self._one("SELECT * FROM telegram_link_tokens WHERE token = ?", (token,))
        return LinkToken(**row) if row else None

    def use_token(self, token: str, now: str) -> int:
        """Mark used. Returns 0 if someone else used it first."""
        return self._exec(
            "UPDATE telegram_link_tokens SET used_at = ? WHERE token = ? AND used_at IS NULL",
            (now, token),
        )

    @staticmethod
    def _to_chat(row: Row | None) -> TelegramChat | None:
        return TelegramChat(**{**row, "paused": bool(row["paused"])}) if row else None
