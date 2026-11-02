from __future__ import annotations

from ...core.database import Row
from ...core.repository import OwnedRepository
from ..connectors.models import Listing
from .models import PriceChange, StoredListing


class ListingRepository(OwnedRepository):
    """Every flat the user's searches have matched, and how its price moved.

    Search ids are unique across users; ``user_id`` is stored as well so
    reads that span all of a user's searches stay a single filter.
    """

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS listings (
            user_id       TEXT NOT NULL,
            search_id     TEXT NOT NULL,
            key           TEXT NOT NULL,      -- "<source>:<external id>"
            fuzzy_key     TEXT,               -- price|area|place, for cross-portal duplicates
            source        TEXT NOT NULL,
            deal_type     TEXT NOT NULL DEFAULT 'sale',
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
        "CREATE INDEX IF NOT EXISTS listings_user ON listings (user_id, first_seen_at)",
        """CREATE TABLE IF NOT EXISTS price_changes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            search_id  TEXT NOT NULL,
            key        TEXT NOT NULL,
            old_price  INTEGER NOT NULL,
            new_price  INTEGER NOT NULL,
            changed_at TEXT NOT NULL
        )""",
    )

    def get(self, search_id: str, key: str) -> StoredListing | None:
        row = self._one(
            "SELECT * FROM listings WHERE user_id = ? AND search_id = ? AND key = ?", (self.user_id, search_id, key)
        )
        return self._to_stored(row) if row else None

    def has_twin(self, search_id: str, fuzzy_key: str, source: str) -> bool:
        """Is the same flat already stored from a *different* portal?"""
        row = self._one(
            "SELECT 1 AS hit FROM listings WHERE user_id = ? AND search_id = ? AND fuzzy_key = ? AND source != ? LIMIT 1",
            (self.user_id, search_id, fuzzy_key, source),
        )
        return row is not None

    def insert(self, search_id: str, deal_type: str, listing: Listing, fuzzy_key: str | None, now: str) -> None:
        self._exec(
            """INSERT INTO listings (user_id, search_id, key, fuzzy_key, source, deal_type, url, title, price, area,
                                     rooms, location, image_url, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.user_id, search_id, listing.key, fuzzy_key, listing.source, deal_type, listing.url, listing.title, listing.price,
             listing.area, listing.rooms, listing.location, listing.image_url, now, now),
        )

    def touch(self, search_id: str, key: str, price: int | None, now: str) -> None:
        self._exec(
            "UPDATE listings SET price = ?, last_seen_at = ? WHERE user_id = ? AND search_id = ? AND key = ?",
            (price, now, self.user_id, search_id, key),
        )

    def add_price_change(self, search_id: str, key: str, old_price: int, new_price: int, now: str) -> None:
        self._exec(
            "INSERT INTO price_changes (user_id, search_id, key, old_price, new_price, changed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (self.user_id, search_id, key, old_price, new_price, now),
        )

    def latest(self, search_id: str | None, limit: int) -> list[StoredListing]:
        if search_id:
            rows = self._all(
                "SELECT * FROM listings WHERE user_id = ? AND search_id = ? ORDER BY first_seen_at DESC, key LIMIT ?",
                (self.user_id, search_id, limit),
            )
        else:
            rows = self._all(
                "SELECT * FROM listings WHERE user_id = ? ORDER BY first_seen_at DESC, key LIMIT ?", (self.user_id, limit)
            )
        return [self._to_stored(row) for row in rows]

    def price_changes(self, limit: int) -> list[PriceChange]:
        rows = self._all(
            """SELECT p.search_id, p.key, l.title, l.url, p.old_price, p.new_price, p.changed_at
               FROM price_changes p JOIN listings l ON l.search_id = p.search_id AND l.key = p.key
               WHERE p.user_id = ?
               ORDER BY p.changed_at DESC, p.id DESC LIMIT ?""",
            (self.user_id, limit),
        )
        return [PriceChange(**row) for row in rows]

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM listings WHERE user_id = ?", (self.user_id,))["n"]

    @staticmethod
    def _to_stored(row: Row) -> StoredListing:
        return StoredListing(**{key: value for key, value in row.items() if key not in ("fuzzy_key", "user_id")})
