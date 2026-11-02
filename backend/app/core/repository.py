"""Base class for every repository."""

from __future__ import annotations

from .database import Database, Params, Row


class BaseRepository:
    """Owns a set of tables in one database.

    Subclasses declare ``SCHEMA`` — idempotent ``CREATE … IF NOT EXISTS``
    statements — and get ``migrate()`` for free. Keeping the DDL next to the
    queries that use it means a table has exactly one owner.
    """

    SCHEMA: tuple[str, ...] = ()
    #: Columns added after a table first shipped: (table, column, definition).
    #: ``CREATE TABLE IF NOT EXISTS`` leaves existing tables alone, so these are
    #: added with ``ALTER TABLE`` wherever they are missing.
    ADDED_COLUMNS: tuple[tuple[str, str, str], ...] = ()

    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def schema(cls) -> tuple[str, ...]:
        return cls.SCHEMA

    def migrate(self) -> None:
        for statement in self.SCHEMA:
            self.db.execute(statement)
        for table, column, definition in self.ADDED_COLUMNS:
            existing = {row["name"] for row in self.db.query(f"PRAGMA table_info({table})")}
            if column not in existing:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _one(self, sql: str, params: Params = ()) -> Row | None:
        return self.db.query_one(sql, params)

    def _all(self, sql: str, params: Params = ()) -> list[Row]:
        return self.db.query(sql, params)

    def _exec(self, sql: str, params: Params = ()) -> int:
        return self.db.execute(sql, params)
