from __future__ import annotations

from pathlib import Path

from ....core.database import Database, SqliteDatabase
from ..models import DatabaseCredentials, Tenant
from .base import ProvisionedDatabase, TenantProvisioner


class SqliteTenantProvisioner(TenantProvisioner):
    """One SQLite file per user. For local development and tests.

    A file on the server is not reachable from the user's machine, so the
    "credentials" are the path — useful for debugging, and the export
    endpoint gives users the same file to download.
    """

    name = "sqlite"

    def __init__(self, directory: str):
        self._directory = Path(directory)

    def create(self, user_id: str) -> ProvisionedDatabase:
        name = self.db_name_for(user_id)
        path = self._directory / f"{name}.db"
        return ProvisionedDatabase(db_name=name, db_url=f"sqlite:///{path}", db_token="")

    def open(self, tenant: Tenant) -> Database:
        return SqliteDatabase(tenant.db_url[len("sqlite:///"):])

    def issue_credentials(self, tenant: Tenant, read_only: bool) -> DatabaseCredentials:
        return DatabaseCredentials(
            provider=self.name,
            url=tenant.db_url,
            token="",
            read_only=read_only,
            how_to_connect="Local development database. Download it with the export button and open it with any SQLite client.",
        )
