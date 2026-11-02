from __future__ import annotations

from ...core.database import Database
from ...core.repository import BaseRepository, OwnedRepository
from ..connectors.models import Listing
from .models import Match, PriceChange, StoredListing


class ListingCatalog(BaseRepository):
    """Every offer seen on a portal, stored once however many searches match it.

    Its price history is shared too. Who an offer was matched for lives in
    ``ListingRepository`` as a small row of ids.
    """

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS portal_listings (
            key           TEXT PRIMARY KEY,   -- "<source>:<external id>"
            fuzzy_key     TEXT,               -- price|area|place, for cross-portal duplicates
            source        TEXT NOT NULL,
            deal_type     TEXT NOT NULL,
            url           TEXT NOT NULL,
            title         TEXT NOT NULL,
            price         INTEGER,
            area          REAL,
            rooms         INTEGER,
            location      TEXT,
            image_url     TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS listing_prices (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            key        TEXT NOT NULL,
            old_price  INTEGER NOT NULL,
            new_price  INTEGER NOT NULL,
            changed_at TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS listing_prices_key ON listing_prices (key, changed_at)",
    )

    @classmethod
    def create_tables(cls, db: Database) -> None:
        super().create_tables(db)
        ListingRepository.create_tables(db)
        _adopt_per_user_tables(db)

    def known(self, key: str) -> tuple[int | None, str] | None:
        """The stored price and when the offer was last seen, or None for a new offer."""
        row = self._one("SELECT price, last_seen_at FROM portal_listings WHERE key = ?", (key,))
        return (row["price"], row["last_seen_at"]) if row else None

    def insert(self, listing: Listing, deal_type: str, fuzzy_key: str | None, now: str) -> None:
        self._exec(
            """INSERT INTO portal_listings (key, fuzzy_key, source, deal_type, url, title, price, area, rooms,
                                            location, image_url, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (listing.key, fuzzy_key, listing.source, deal_type, listing.url, listing.title, listing.price,
             listing.area, listing.rooms, listing.location, listing.image_url, now, now),
        )

    def seen(self, key: str, price: int | None, now: str) -> None:
        self._exec("UPDATE portal_listings SET price = ?, last_seen_at = ? WHERE key = ?", (price, now, key))

    def drop_unmatched(self) -> int:
        """Offers no search points to any more, and their price history."""
        self._exec("DELETE FROM listing_prices WHERE key NOT IN (SELECT key FROM search_matches)")
        return self._exec("DELETE FROM portal_listings WHERE key NOT IN (SELECT key FROM search_matches)")

    def add_price_change(self, key: str, old_price: int, new_price: int, now: str) -> None:
        self._exec(
            "INSERT INTO listing_prices (key, old_price, new_price, changed_at) VALUES (?, ?, ?, ?)",
            (key, old_price, new_price, now),
        )


class ListingRepository(OwnedRepository):
    """Which offers each of the user's searches matched, and the price the user last heard."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS search_matches (
            search_id  TEXT NOT NULL,
            key        TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            price_seen INTEGER,
            matched_at TEXT NOT NULL,
            PRIMARY KEY (search_id, key)
        )""",
        "CREATE INDEX IF NOT EXISTS search_matches_user ON search_matches (user_id, matched_at)",
        "CREATE INDEX IF NOT EXISTS search_matches_key ON search_matches (key)",
    )

    _LISTING = """m.search_id, l.key, l.source, l.deal_type, l.url, l.title, l.price, l.area, l.rooms, l.location,
                  l.image_url, m.matched_at AS first_seen_at, l.last_seen_at
                  FROM search_matches m JOIN portal_listings l ON l.key = m.key"""

    def match(self, search_id: str, key: str) -> Match | None:
        row = self._one(
            "SELECT price_seen FROM search_matches WHERE user_id = ? AND search_id = ? AND key = ?",
            (self.user_id, search_id, key),
        )
        return Match(price_seen=row["price_seen"]) if row else None

    def has_twin(self, search_id: str, fuzzy_key: str, source: str) -> bool:
        """Has this search already matched the same flat from a *different* portal?"""
        row = self._one(
            """SELECT 1 AS hit FROM search_matches m JOIN portal_listings l ON l.key = m.key
               WHERE m.user_id = ? AND m.search_id = ? AND l.fuzzy_key = ? AND l.source != ? LIMIT 1""",
            (self.user_id, search_id, fuzzy_key, source),
        )
        return row is not None

    def add(self, search_id: str, key: str, price: int | None, now: str) -> None:
        self._exec(
            "INSERT INTO search_matches (search_id, key, user_id, price_seen, matched_at) VALUES (?, ?, ?, ?, ?)",
            (search_id, key, self.user_id, price, now),
        )

    def set_price_seen(self, search_id: str, key: str, price: int | None) -> None:
        self._exec(
            "UPDATE search_matches SET price_seen = ? WHERE user_id = ? AND search_id = ? AND key = ?",
            (price, self.user_id, search_id, key),
        )

    def latest(self, search_id: str | None, limit: int) -> list[StoredListing]:
        if search_id:
            rows = self._all(
                f"SELECT {self._LISTING} WHERE m.user_id = ? AND m.search_id = ? ORDER BY m.matched_at DESC, m.key LIMIT ?",
                (self.user_id, search_id, limit),
            )
        else:
            rows = self._all(
                f"SELECT {self._LISTING} WHERE m.user_id = ? ORDER BY m.matched_at DESC, m.key LIMIT ?",
                (self.user_id, limit),
            )
        return [StoredListing(**row) for row in rows]

    def price_changes(self, limit: int) -> list[PriceChange]:
        """Changes to offers the user had, from the moment each was matched."""
        rows = self._all(
            """SELECT m.search_id, p.key, l.title, l.url, p.old_price, p.new_price, p.changed_at
               FROM listing_prices p
               JOIN search_matches m ON m.key = p.key AND p.changed_at >= m.matched_at
               JOIN portal_listings l ON l.key = p.key
               WHERE m.user_id = ?
               ORDER BY p.changed_at DESC, p.id DESC LIMIT ?""",
            (self.user_id, limit),
        )
        return [PriceChange(**row) for row in rows]

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM search_matches WHERE user_id = ?", (self.user_id,))["n"]

    def forget_search(self, search_id: str) -> None:
        self._exec("DELETE FROM search_matches WHERE user_id = ? AND search_id = ?", (self.user_id, search_id))


def _adopt_per_user_tables(db: Database) -> None:
    """Move rows from the earlier layout, where each user kept a full copy of every offer."""
    tables = {row["name"] for row in db.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "listings" not in tables:
        return
    db.execute(
        """INSERT OR IGNORE INTO portal_listings (key, fuzzy_key, source, deal_type, url, title, price, area, rooms,
                                                  location, image_url, first_seen_at, last_seen_at)
           SELECT key, fuzzy_key, source, deal_type, url, title, price, area, rooms, location, image_url,
                  MIN(first_seen_at), MAX(last_seen_at)
           FROM listings GROUP BY key"""
    )
    db.execute(
        """INSERT OR IGNORE INTO search_matches (search_id, key, user_id, price_seen, matched_at)
           SELECT search_id, key, user_id, price, first_seen_at FROM listings"""
    )
    if "price_changes" in tables:
        db.execute(
            """INSERT INTO listing_prices (key, old_price, new_price, changed_at)
               SELECT DISTINCT key, old_price, new_price, changed_at FROM price_changes"""
        )
        db.execute("DROP TABLE price_changes")
    db.execute("DROP TABLE listings")
