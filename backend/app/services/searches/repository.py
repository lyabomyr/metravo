from __future__ import annotations

import json

from ...core.database import Row
from ...core.repository import BaseRepository
from ..connectors.models import DealType, PropertyType
from .models import Search


class SearchRepository(BaseRepository):
    """Tenant database: the user's saved searches."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS searches (
            id              TEXT PRIMARY KEY,
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
            enabled         INTEGER NOT NULL DEFAULT 1,
            last_scanned_at TEXT,
            created_at      TEXT NOT NULL
        )""",
    )

    _COLUMNS = (
        "id", "name", "city", "deal_type", "property_type", "min_price", "max_price", "min_area", "max_area",
        "min_rooms", "max_rooms", "max_price_per_m2", "min_build_year", "sources", "required_keywords",
        "reject_keywords", "enabled", "last_scanned_at", "created_at",
    )

    def all(self) -> list[Search]:
        return [self._to_search(row) for row in self._all("SELECT * FROM searches ORDER BY created_at")]

    def by_id(self, search_id: str) -> Search | None:
        row = self._one("SELECT * FROM searches WHERE id = ?", (search_id,))
        return self._to_search(row) if row else None

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM searches")["n"]

    def save(self, search: Search) -> None:
        placeholders = ", ".join("?" for _ in self._COLUMNS)
        self._exec(
            f"INSERT OR REPLACE INTO searches ({', '.join(self._COLUMNS)}) VALUES ({placeholders})",
            self._to_row(search),
        )

    def delete(self, search_id: str) -> int:
        return self._exec("DELETE FROM searches WHERE id = ?", (search_id,))

    def mark_scanned(self, search_id: str, at: str) -> None:
        self._exec("UPDATE searches SET last_scanned_at = ? WHERE id = ?", (at, search_id))

    def set_enabled_all(self, enabled: bool) -> None:
        self._exec("UPDATE searches SET enabled = ?", (int(enabled),))

    @staticmethod
    def _to_row(search: Search) -> tuple:
        return (
            search.id, search.name, search.city, search.deal_type.value, search.property_type.value,
            search.min_price, search.max_price, search.min_area, search.max_area, search.min_rooms, search.max_rooms,
            search.max_price_per_m2, search.min_build_year, json.dumps(search.sources),
            json.dumps(search.required_keywords, ensure_ascii=False), json.dumps(search.reject_keywords, ensure_ascii=False),
            int(search.enabled), search.last_scanned_at, search.created_at,
        )

    @staticmethod
    def _to_search(row: Row) -> Search:
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
