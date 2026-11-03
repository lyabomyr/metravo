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
        # Which searches a chat in "only selected" mode hears.
        """CREATE TABLE IF NOT EXISTS telegram_routes (
            chat_id   TEXT NOT NULL,
            search_id TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            PRIMARY KEY (chat_id, search_id)
        )""",
        "CREATE INDEX IF NOT EXISTS telegram_routes_search ON telegram_routes (user_id, search_id)",
    )
    ADDED_COLUMNS = (
        ("telegram_chats", "only_selected", "INTEGER NOT NULL DEFAULT 0"),
        ("telegram_link_tokens", "search_id", "TEXT"),
    )

    # --- chats -----------------------------------------------------------

    def chat(self, chat_id: str) -> TelegramChat | None:
        return self._to_chat(self._one("SELECT * FROM telegram_chats WHERE chat_id = ?", (chat_id,)))

    def chats_of(self, user_id: str) -> list[TelegramChat]:
        rows = self._all("SELECT * FROM telegram_chats WHERE user_id = ? ORDER BY linked_at", (user_id,))
        return [self._to_chat(row) for row in rows]

    def link_chat(self, chat_id: str, user_id: str, title: str, now: str, only_selected: bool = False) -> None:
        self._exec("DELETE FROM telegram_routes WHERE chat_id = ?", (chat_id,))
        self._exec(
            """INSERT OR REPLACE INTO telegram_chats (chat_id, user_id, title, paused, linked_at, only_selected)
               VALUES (?, ?, ?, 0, ?, ?)""",
            (chat_id, user_id, title, now, int(only_selected)),
        )

    def unlink_chat(self, chat_id: str) -> int:
        self._exec("DELETE FROM telegram_routes WHERE chat_id = ?", (chat_id,))
        return self._exec("DELETE FROM telegram_chats WHERE chat_id = ?", (chat_id,))

    def move_chat(self, old_id: str, new_id: str) -> int:
        self._exec("UPDATE telegram_routes SET chat_id = ? WHERE chat_id = ?", (new_id, old_id))
        return self._exec("UPDATE telegram_chats SET chat_id = ? WHERE chat_id = ?", (new_id, old_id))

    # --- routes: which searches a chat hears -----------------------------

    def set_only_selected(self, chat_id: str, only_selected: bool) -> None:
        self._exec("UPDATE telegram_chats SET only_selected = ? WHERE chat_id = ?", (int(only_selected), chat_id))

    def routed_searches(self, chat_id: str) -> set[str]:
        return {row["search_id"] for row in self._all("SELECT search_id FROM telegram_routes WHERE chat_id = ?", (chat_id,))}

    def add_route(self, chat_id: str, search_id: str, user_id: str) -> None:
        self._exec(
            "INSERT OR IGNORE INTO telegram_routes (chat_id, search_id, user_id) VALUES (?, ?, ?)",
            (chat_id, search_id, user_id),
        )

    def drop_route(self, chat_id: str, search_id: str) -> None:
        self._exec("DELETE FROM telegram_routes WHERE chat_id = ? AND search_id = ?", (chat_id, search_id))

    def forget_search_routes(self, user_id: str, search_id: str) -> None:
        self._exec("DELETE FROM telegram_routes WHERE user_id = ? AND search_id = ?", (user_id, search_id))

    def set_paused(self, chat_id: str, paused: bool) -> None:
        self._exec("UPDATE telegram_chats SET paused = ? WHERE chat_id = ?", (int(paused), chat_id))

    def count_chats(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM telegram_chats")["n"]

    # --- link tokens -----------------------------------------------------

    def add_token(self, token: str, user_id: str, expires_at: str, search_id: str | None = None) -> None:
        self._exec(
            "INSERT INTO telegram_link_tokens (token, user_id, expires_at, search_id) VALUES (?, ?, ?, ?)",
            (token, user_id, expires_at, search_id),
        )

    def drop_tokens_expired_before(self, before: str) -> int:
        return self._exec("DELETE FROM telegram_link_tokens WHERE expires_at < ?", (before,))

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
        if not row:
            return None
        return TelegramChat(**{**row, "paused": bool(row["paused"]), "only_selected": bool(row["only_selected"])})
