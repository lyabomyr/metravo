from __future__ import annotations

from ...core.database import Row
from ...core.repository import BaseRepository
from .models import Tenant


class TenantRepository(BaseRepository):
    """Control database: which database belongs to which user."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS tenants (
            user_id    TEXT PRIMARY KEY,
            provider   TEXT NOT NULL,
            db_name    TEXT NOT NULL,
            db_url     TEXT NOT NULL,
            db_token   TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )""",
    )

    def by_user(self, user_id: str) -> Tenant | None:
        return self._to_tenant(self._one("SELECT * FROM tenants WHERE user_id = ?", (user_id,)))

    def insert(self, tenant: Tenant) -> None:
        self._exec(
            "INSERT INTO tenants (user_id, provider, db_name, db_url, db_token, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (tenant.user_id, tenant.provider, tenant.db_name, tenant.db_url, tenant.db_token, tenant.created_at),
        )

    def all(self) -> list[Tenant]:
        return [self._to_tenant(row) for row in self._all("SELECT * FROM tenants ORDER BY created_at")]

    def count(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM tenants")["n"]

    @staticmethod
    def _to_tenant(row: Row | None) -> Tenant | None:
        return Tenant(**row) if row else None
