from __future__ import annotations

from ...core.database import Row
from ...core.repository import BaseRepository
from ..connectors.models import Listing
from .models import PriceChange, StoredListing


class ListingRepository(BaseRepository):
    """Tenant database: every flat a search has matched, and how its price moved."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS listings (
            search_id     TEXT NOT NULL,
            key           TEXT NOT NULL,      -- "<source>:<external id>"
            fuzzy_key     TEXT,               -- price|area|place, for cross-portal duplicates
            source        TEXT NOT NULL,
            url           TEXT NOT NULL,
            title         TEXT NOT NULL,
            price         INTEGER,
            area          REAL,
            rooms         INTEGER,
            location      TEXT,
            image_url     TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at  TEXT NOT NULL,
            PRIMARY KEY (search_id, key)
        )""",
        "CREATE INDEX IF NOT EXISTS listings_fuzzy ON listings (search_id, fuzzy_key)",
        """CREATE TABLE IF NOT EXISTS price_changes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id  TEXT NOT NULL,
            key        TEXT NOT NULL,
            old_price  INTEGER NOT NULL,
            new_price  INTEGER NOT NULL,
            changed_at TEXT NOT NULL
        )""",
    )

    def get(self, search_id: str, key: str) -> StoredListing | None:
        row = self._one("SELECT * FROM listings WHERE search_id = ? AND key = ?", (search_id, key))
        return self._to_stored(row) if row else None

    def has_twin(self, search_id: str, fuzzy_key: str, source: str) -> bool:
        """Is the same flat already stored from a *different* portal?"""
        row = self._one(
            "SELECT 1 AS hit FROM listings WHERE search_id = ? AND fuzzy_key = ? AND source != ? LIMIT 1",
            (search_id, fuzzy_key, source),
        )
        return row is not None

    def insert(self, search_id: str, listing: Listing, fuzzy_key: str | None, now: str) -> None:
        self._exec(
            """INSERT INTO listings (search_id, key, fuzzy_key, source, url, title, price, area, rooms,
                                     location, image_url, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (search_id, listing.key, fuzzy_key, listing.source, listing.url, listing.title, listing.price,
             listing.area, listing.rooms, listing.location, listing.image_url, now, now),
        )

    def touch(self, search_id: str, key: str, price: int | None, now: str) -> None:
        self._exec(
            "UPDATE listings SET price = ?, last_seen_at = ? WHERE search_id = ? AND key = ?",
            (price, now, search_id, key),
        )

    def add_price_change(self, search_id: str, key: str, old_price: int, new_price: int, now: str) -> None:
        self._exec(
            "INSERT INTO price_changes (search_id, key, old_price, new_price, changed_at) VALUES (?, ?, ?, ?, ?)",
            (search_id, key, old_price, new_price, now),
        )

    def latest(self, search_id: str | None, limit: int) -> list[StoredListing]:
        if search_id:
            rows = self._all(
                "SELECT * FROM listings WHERE search_id = ? ORDER BY first_seen_at DESC, key LIMIT ?",
                (search_id, limit),
            )
        else:
            rows = self._all("SELECT * FROM listings ORDER BY first_seen_at DESC, key LIMIT ?", (limit,))
        return [self._to_stored(row) for row in rows]

    def price_changes(self, limit: int) -> list[PriceChange]:
        rows = self._all(
            """SELECT p.search_id, p.key, l.title, l.url, p.old_price, p.new_price, p.changed_at
               FROM price_changes p JOIN listings l ON l.search_id = p.search_id AND l.key = p.key
               ORDER BY p.changed_at DESC, p.id DESC LIMIT ?""",
            (limit,),
        )
        return [PriceChange(**row) for row in rows]

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM listings")["n"]

    @staticmethod
    def _to_stored(row: Row) -> StoredListing:
        return StoredListing(**{key: value for key, value in row.items() if key != "fuzzy_key"})
