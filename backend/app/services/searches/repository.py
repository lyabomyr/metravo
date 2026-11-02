from __future__ import annotations

import json

from ...core.database import Database, Row
from ...core.repository import OwnedRepository
from ..connectors.models import DealType, PropertyType
from .models import Search


class SearchRepository(OwnedRepository):
    """The user's saved searches."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS searches (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            name            TEXT NOT NULL,
            city            TEXT NOT NULL,
            deal_type       TEXT NOT NULL DEFAULT 'sale',   -- sale | rent
            property_type   TEXT NOT NULL DEFAULT 'flat',   -- flat | house
            min_price       INTEGER,
            max_price       INTEGER NOT NULL,
            min_area        REAL NOT NULL,
            max_area        REAL,
            min_rooms       INTEGER,
            max_rooms       INTEGER,
            max_price_per_m2 INTEGER,
            min_build_year  INTEGER,
            sources         TEXT NOT NULL,   -- JSON array
            required_keywords TEXT NOT NULL DEFAULT '[]',   -- JSON array
            reject_keywords TEXT NOT NULL,   -- JSON array
            interval_minutes INTEGER NOT NULL DEFAULT 1440,
            enabled         INTEGER NOT NULL DEFAULT 1,
            last_scanned_at TEXT,
            created_at      TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS searches_user ON searches (user_id)",
    )

    _COLUMNS = (
        "id", "user_id", "name", "city", "deal_type", "property_type", "min_price", "max_price", "min_area", "max_area",
        "min_rooms", "max_rooms", "max_price_per_m2", "min_build_year", "sources", "required_keywords",
        "reject_keywords", "interval_minutes", "enabled", "last_scanned_at", "created_at",
    )

    @staticmethod
    def owners(db: Database) -> list[str]:
        """Everyone who has saved a search — the users a scan visits."""
        return [row["user_id"] for row in db.query("SELECT DISTINCT user_id FROM searches ORDER BY user_id")]

    def all(self) -> list[Search]:
        rows = self._all("SELECT * FROM searches WHERE user_id = ? ORDER BY created_at", (self.user_id,))
        return [self._to_search(row) for row in rows]

    def by_id(self, search_id: str) -> Search | None:
        row = self._one("SELECT * FROM searches WHERE id = ? AND user_id = ?", (search_id, self.user_id))
        return self._to_search(row) if row else None

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM searches WHERE user_id = ?", (self.user_id,))["n"]

    def save(self, search: Search) -> None:
        placeholders = ", ".join("?" for _ in self._COLUMNS)
        self._exec(
            f"INSERT OR REPLACE INTO searches ({', '.join(self._COLUMNS)}) VALUES ({placeholders})",
            self._to_row(search),
        )

    def delete(self, search_id: str) -> int:
        return self._exec("DELETE FROM searches WHERE id = ? AND user_id = ?", (search_id, self.user_id))

    def mark_scanned(self, search_id: str, at: str) -> None:
        self._exec("UPDATE searches SET last_scanned_at = ? WHERE id = ? AND user_id = ?", (at, search_id, self.user_id))

    def set_enabled_all(self, enabled: bool) -> None:
        self._exec("UPDATE searches SET enabled = ? WHERE user_id = ?", (int(enabled), self.user_id))

    def _to_row(self, search: Search) -> tuple:
        return (
            search.id, self.user_id, search.name, search.city, search.deal_type.value, search.property_type.value,
            search.min_price, search.max_price, search.min_area, search.max_area, search.min_rooms, search.max_rooms,
            search.max_price_per_m2, search.min_build_year, json.dumps(search.sources),
            json.dumps(search.required_keywords, ensure_ascii=False), json.dumps(search.reject_keywords, ensure_ascii=False),
            search.interval_minutes, int(search.enabled), search.last_scanned_at, search.created_at,
        )

    @staticmethod
    def _to_search(row: Row) -> Search:
        row = {key: value for key, value in row.items() if key != "user_id"}
        return Search(
            **{
                **row,
                "deal_type": DealType(row["deal_type"]),
                "property_type": PropertyType(row["property_type"]),
                "sources": json.loads(row["sources"]),
                "required_keywords": json.loads(row["required_keywords"]),
                "reject_keywords": json.loads(row["reject_keywords"]),
                "enabled": bool(row["enabled"]),
            }
        )
