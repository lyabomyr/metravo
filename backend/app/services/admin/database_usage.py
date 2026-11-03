from __future__ import annotations

import logging
from dataclasses import dataclass

from ...core.database import Database

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableUsage:
    name: str
    rows: int
    #: Pages on disk, its indexes included; None where the engine does not report it.
    bytes: int | None


class DatabaseUsage:
    """What fills the database: every table with its rows and size, the biggest first.

    Lists every table in the file, ours or not, so leftovers of other tools show up too.
    """

    def __init__(self, db: Database):
        self._db = db

    def tables(self) -> list[TableUsage]:
        names = [row["name"] for row in self._db.query(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '\\_%' ESCAPE '\\'"
        )]
        sizes = self._sizes()
        tables = [TableUsage(name, self._count(name), sizes.get(name)) for name in names]
        return sorted(tables, key=lambda table: (table.bytes or 0, table.rows), reverse=True)

    def _count(self, table: str) -> int:
        quoted = table.replace('"', '""')
        return self._db.query_one(f'SELECT COUNT(*) AS n FROM "{quoted}"')["n"]

    def _sizes(self) -> dict[str, int]:
        try:
            pages = self._db.query("SELECT name, SUM(pgsize) AS size FROM dbstat GROUP BY name")
        except Exception as error:  # noqa: BLE001 — dbstat is optional in SQLite builds
            log.info("table sizes unavailable: %s", error)
            return {}
        owner = {row["name"]: row["tbl_name"] for row in self._db.query("SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'")}
        sizes: dict[str, int] = {}
        for row in pages:
            table = owner.get(row["name"], row["name"])
            sizes[table] = sizes.get(table, 0) + (row["size"] or 0)
        return sizes
