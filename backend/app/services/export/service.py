from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

from ...core.database import Database, SqliteDatabase
from ...core.service import BaseService
from ..tenants.service import TenantService
from ..users.models import User

LISTING_CSV_COLUMNS = ("search_id", "source", "title", "price", "area", "rooms", "location", "url", "first_seen_at", "last_seen_at")


class ExportService(BaseService):
    """Hands users their data. Available on every plan — it is their data."""

    def __init__(self, tenants: TenantService):
        super().__init__()
        self._tenants = tenants

    def sqlite_file(self, user: User) -> bytes:
        """A complete copy of the user's database as a standalone SQLite file."""
        source = self._tenants.database_for(user.id)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metravo.db"
            target = SqliteDatabase(str(path))
            for statement in self._tenants.schema():
                target.execute(statement)
            for table in self._tables(source):
                self._copy_table(source, target, table)
            target.close()
            return path.read_bytes()

    def listings_csv(self, user: User) -> str:
        rows = self._tenants.database_for(user.id).query(
            f"SELECT {', '.join(LISTING_CSV_COLUMNS)} FROM listings ORDER BY first_seen_at DESC"
        )
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=LISTING_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

    @staticmethod
    def _tables(db: Database) -> list[str]:
        rows = db.query("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        return [row["name"] for row in rows]

    @staticmethod
    def _copy_table(source: Database, target: Database, table: str) -> None:
        for row in source.query(f'SELECT * FROM "{table}"'):
            columns = ", ".join(f'"{column}"' for column in row)
            placeholders = ", ".join("?" for _ in row)
            target.execute(f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})', tuple(row.values()))
