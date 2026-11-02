from __future__ import annotations

import csv
import io

from ...core.database import Database
from ...core.service import BaseService
from ..users.models import User

LISTING_CSV_COLUMNS = (
    "search", "source", "title", "price", "area", "rooms", "price_per_m2", "location", "url", "first_seen_at", "last_seen_at",
)


class ExportService(BaseService):
    """Hands users their data as a spreadsheet. Every plan — it is their data."""

    def __init__(self, db: Database):
        super().__init__()
        self._db = db

    def listings_csv(self, user: User) -> str:
        rows = self._db.query(
            """SELECT s.name AS search, l.source, l.title, l.price, l.area, l.rooms,
                      CASE WHEN l.price IS NOT NULL AND l.area > 0 THEN CAST(ROUND(l.price / l.area) AS INTEGER) END
                          AS price_per_m2,
                      l.location, l.url, l.first_seen_at, l.last_seen_at
               FROM listings l LEFT JOIN searches s ON s.id = l.search_id
               WHERE l.user_id = ?
               ORDER BY l.first_seen_at DESC, l.key""",
            (user.id,),
        )
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=LISTING_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()
