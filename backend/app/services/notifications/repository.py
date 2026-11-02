from __future__ import annotations

from ...core.repository import BaseRepository


class NotificationRepository(BaseRepository):
    """Control database: which channels each user wants listings on."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS notification_settings (
            user_id    TEXT NOT NULL,
            channel    TEXT NOT NULL,
            enabled    INTEGER NOT NULL,
            address    TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, channel)
        )""",
    )

    def of(self, user_id: str) -> dict[str, tuple[bool, str]]:
        rows = self._all("SELECT channel, enabled, address FROM notification_settings WHERE user_id = ?", (user_id,))
        return {row["channel"]: (bool(row["enabled"]), row["address"]) for row in rows}

    def save(self, user_id: str, channel: str, enabled: bool, address: str, now: str) -> None:
        self._exec(
            "INSERT OR REPLACE INTO notification_settings (user_id, channel, enabled, address, updated_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, channel, int(enabled), address, now),
        )
